#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import gc
import gflags
import warnings
from jinja2 import Template

from pygaga.helpers.mapreduce_multiprocessing import SimpleMapReduce

logger = logging.getLogger('PygagaModel')

FLAGS = gflags.FLAGS
gflags.DEFINE_boolean('remove_tmp_data', True, "Is remove temp model data")
gflags.DEFINE_integer('logit_split_rows', 10, "Split Rows")
gflags.DEFINE_integer('logit_split_cols', 12, "Split Cols")
gflags.DEFINE_string('family', 'binomial', "binomial or poisson")
gflags.DEFINE_string('svd_cmd', '/usr/local/bin/svd', "path of svd command")
gflags.DEFINE_string('liblinear_cmd', '/usr/local/bin/liblinear_train', "liblinear command")

def render(r_name, context):
    #print "rendering", r_name, context
    _mod_path = os.path.split(__file__)[0]
    r_src = open(os.path.join(_mod_path, "r/" + r_name)).read()
    template = Template(r_src)
    return template.render(context)

def get_tmpfile(prefix="file"):
    return os.tempnam("tmp", prefix)

def remove_file(f):
    if FLAGS.remove_tmp_data:
        os.remove(f)

def split_rows(file, n = 10):
    "将样本切分为n 份，返回文件名数组"
    logger.debug("split by row")
    ls = open(file).readlines()
    ave = len(ls) / n
    residue = len(ls) % n
    filenames = []
    start = 0
    for i in range(n):
        fname = get_tmpfile("sprow")
        filenames.append(fname)
        fp = open(fname, 'w')

        if i < residue:
            step = ave + 1
        else:
            step = ave
        fp.write(ls[0])
        for j in range(1 + start, min(1 + start + step, len(ls))):
            fp.write(ls[j])
        fp.write("\n")
        fp.close()
        #print >> open(fname,'w'), ls[0]+''.join(ls[1+start:1+start + step])
        start += step
    del ls
    gc.collect()
    return filenames

def run_r(r_script, prefix="runr1_"):
    "运行R 脚本"
    fname = "%s.r" % get_tmpfile(prefix)
    print >> open(fname, 'w'), r_script
    ret = os.system("R --slave --no-save -f %s" % fname)
    if ret != 0:
         raise Exception("run r error r_script=%s exit_code=%s" % (fname, ret))

    remove_file(fname)

def split_columns_map(arg):
    "使用R 将数据纵向切分为n 份"
    file, n = arg
    filenames = []
    for _ in range(n):
        filenames.append(get_tmpfile("splcol"))
    r_script = render("split_columns.r", {'row_file':file,
                                          'split_count':n,
                                          'filenames':filenames,
                                          })
    run_r(r_script, "runrsplit_")
    return ((file, filenames), )

def feature_select_map(arg):
    "并行运算R 脚本，变量选择时用"
    r_script = arg
    run_r(r_script, "runrfs_")
    return ((0, 0), )

def identity_reduce(item):
    "简单reducer，输出第一个value"
    _, v = item
    return v[0]

def select_feature(row_filenames, cols=12):
    "对每个变量进行单变量逻辑回归，选出p 值小于0.1 的，由于内存限制，最多选择400个"
    logger.debug("split feature by cols %s" % row_filenames)

    # 将数据按照变量切分为 column_blocks 块，以便并行计算
    split_mapper = SimpleMapReduce(split_columns_map, identity_reduce)

    column_blocks = cols
    arg = []
    for i in row_filenames:
        arg.append((i, column_blocks))
    column_filenames = split_mapper(arg)

    logger.debug("selecting feature")
    # 生成对每块计算的R 脚本
    r_scripts = []
    feature_files = []
    for i in range(column_blocks):
        feature_file = get_tmpfile("selfea")
        feature_files.append(feature_file)
        r_script = render("select_feature.r", {'column_filenames' : [cf[i] for cf in column_filenames],
                                               'feature_file' : feature_file,
                                               'family' : FLAGS.family,
                                               })
        r_scripts.append(r_script)

    # 并行计算进行变量选择
    mapper = SimpleMapReduce(feature_select_map, identity_reduce)
    mapper(r_scripts)

    for f in column_filenames:
        for i in f:
            remove_file(i)

    logger.debug("merging features")
    # 将输出归并至一个文件，并进行排序选择
    select_feature_file = get_tmpfile("merge")
    r_script = render("merge_feature.r", {'column_blocks':range(column_blocks),
                                          'select_feature_file':select_feature_file,
                                          'feature_files':feature_files,
                                           })
    run_r(r_script, "runrmg_")

    for i in feature_files:
        remove_file(i)

    return select_feature_file

def generate_strip_data(files, features):
    "从数据中删除未被选上的变量"
    logger.debug("generating strip data")
    strip_data_file = get_tmpfile("genstrip")

    r_script = render("generate_strip_data.r", {'features':features,
                                          'files':files,
                                          'strip_data_file':strip_data_file,
                                           })
    run_r(r_script, "runrstrip_")
    for i in files:
        remove_file(i)
    remove_file(features)
    return strip_data_file

def generate_model(data_file, output_file, use_pca=True):
    logger.debug("running logit regression")

    # 进行逻辑回归
    if use_pca:
        r_script = render("logit_glm.r", {'data_file' : data_file,
                                      'output_file' : output_file,
                                      'family' : FLAGS.family,
                                     })
        run_r(r_script, "runrglm_%s_" % FLAGS.family)
    else:
        r_script = render("logit_nopca_glm.r", {'data_file' : data_file,
                                      'output_file' : output_file,
                                      'family' : FLAGS.family,
                                     })
        run_r(r_script, "runrglm_nopca_%s_" % FLAGS.family)

    remove_file(data_file)

def regression(input_file, output_file, use_pca=True):
    """
    row : 并行运行时数据按行拆分为
    对input_file 的内容进行变量选择及逻辑回归
    """

    rows=FLAGS.logit_split_rows
    cols=FLAGS.logit_split_cols

    warnings.filterwarnings("ignore",
                            "tempnam is a potential security risk to your program")

    try:
        os.mkdir("tmp")
    except:
        pass

    # 因为内存受限，将样本切分
    row_filenames = split_rows(input_file, rows)

    # 对切分后样本进行变量选择，并行
    select_feature_file = select_feature(row_filenames, cols)

    # 将数据中未被选择变量删除
    strip_data_file = generate_strip_data(row_filenames, select_feature_file)

    # 回归，输出
    generate_model(strip_data_file, output_file, use_pca)

    if FLAGS.remove_tmp_data:
        try:
            os.removedirs("tmp")
        except:
            pass

def trans_matrix(m):
    row = len(m)
    col = len(m[0])

    matrix = [[m[j][i] for j in range(0, row)] for i in range(0, col)]
    row, col = col, row

    return (row, col, matrix)

def gen_y_file(data_file, output_file, with_header = True, y_column = -1):
    """抽取数据文件中的Y值
    y_column = -1 表示Y值在最后一列
    """
    header = with_header
    fp = file(output_file, "w")

    for line in file(data_file):
        if header:
            header = False
            continue
        fp.write("%s\n" % line.replace('"', '').split()[y_column])

    fp.close()

def gen_x_file(data_file, output_file, with_header = True):
    """抽取数据文件中的X值(除最后一列)
    """
    header = with_header
    fp = file(output_file, "w")

    for line in file(data_file):
        if header:
            header = False
            continue
        fp.write("%s\n" % line.replace('"', '').rsplit(' ', 1)[0])

    fp.close()

def gen_x_y_file(input_file, with_header = True):
    """把数据文件中的X和Y分开,不保存header"""
    x_file_path = "%s/%s_X" % (os.path.dirname(input_file), os.path.basename(input_file))
    gen_x_file(input_file, x_file_path, with_header = with_header)

    y_file_path = "%s/%s_Y" % (os.path.dirname(input_file), os.path.basename(input_file))
    gen_y_file(input_file, y_file_path, with_header = with_header)

    return x_file_path, y_file_path

def gen_svd_input(data_file, add_1_end = True, output_dir = ""):
    """把从session中选取的训练样本数据转化成svd输入

    add_1_end = True: 在数据文件的最后一行添加常数项的系数，全部为1

    生成svdin文件, 格式: 第一行为输入数据的行、列
    临时result文件,记录训练样本的Y值。供生成liblinear需要的权重文件使用。
    """

    if not output_dir:
        output_dir = os.path.dirname(data_file)
    if not output_dir.endswith("/"):
        output_dir += "/"

    svdin_file_path = "%s%s_svdin" % (output_dir, os.path.basename(data_file))
    svdin_file = file(svdin_file_path, "w")

    result = []
    row = os.popen("wc -l %s" % (data_file)).read().split()[0]
    col = os.popen("head -1 %s | awk '{print NF}'" % (data_file)).read().split()[0]
    if add_1_end:
        col = int(col) + 1

    #出去第一行(变量名),最后一列(Y值)
    svdin_file.write("%s %s" % (int(row) - 1, int(col) - 1))
    first = 0

    #sparse_matrix[i]: 第i列所有非0元素的[(行号,值)...]
    sparse_matrix = []
    for i in range(int(col) - 1):
        sparse_matrix.append([])
    num_nozero = 0
    lineno = 0

    for line in file(data_file):
        ##buggy:: wrong row and col number
        ##TODO densy version
        if not line.strip():
            continue
        if not first:
            first = 1
            continue

        line_columns = line.replace("\"", "").split()
        colno = 0
        #最后一列是Y值
        for item in line_columns[:-1]:
            if float(item) > 0.000001 or float(item) < -0.000001:
                sparse_matrix[colno].append([str(lineno), item])
                num_nozero += 1

            colno += 1

        if add_1_end:
            sparse_matrix[colno].append([str(lineno), '1'])
            num_nozero += 1

        lineno += 1

    #svd spar matrix format: http://tedlab.mit.edu/~dr/SVDLIBC/SVD_F_ST.html
    #numRows numCols totalNonZeroValues
    #for each column:
    #      numNonZeroValues
    #      for each non-zero value in the column:
    #              rowIndex value

    svdin_file.write(" %s\n" % num_nozero)
    for col_nozero in sparse_matrix:
        svdin_file.write("%s\n" % len(col_nozero))
        for item in col_nozero:
            svdin_file.write("%s\n" % ' '.join(item))

    svdin_file.close()

    return svdin_file_path

def run_svd(input_file, max_dim = 1000, max_dim_ratio = 0.3):
    col = int(os.popen("head -1 %s" % input_file).read().split()[1])
    col = int(max_dim_ratio * col)
    output_prefix = input_file.replace("svdin", "svdout")

    dim = min(col, max_dim)

    #svd_cmd = "%s -d %s -r st -o %s %s" % (FLAGS.svd_cmd, dim, output_prefix, input_file)
    svd_cmd = "%s -v 0 -r st -o %s %s" % (FLAGS.svd_cmd, output_prefix, input_file)
    logger.info(svd_cmd)
    os.system(svd_cmd)
    ufile = "%s-Ut" % output_prefix
    vfile = "%s-Vt" % output_prefix
    sfile = "%s-S" %  output_prefix

    ufile_new = "%s-Ut1" % output_prefix
    vfile_new = "%s-Vt1" % output_prefix
    sfile_new = "%s-S1" %  output_prefix

    #select col by Feature value desc, write u,s,v
    ufile_new_fd = file(ufile_new, "w")
    vfile_new_fd = file(vfile_new, "w")
    sfile_new_fd = file(sfile_new, "w")

    s_value = []
    for i, line in enumerate(file(sfile, "r")):
        if i == 0:
            continue
        value = float(line.strip())
        #featue threshold
        if value > 0.000001:
            s_value.append(float(line.strip()))
        else:
            break
    if len(s_value) > 1000:
        s_sum = sum(s_value)
        i = 0
        for i in range(len(s_value)):
            if sum(s_value[:i]) > s_sum * 0.9:
                break
        s_value = s_value[:i]
    fea_len = len(s_value)
    sfile_new_fd.write("%s\n" % fea_len)
    for v in s_value:
        sfile_new_fd.write("%s\n" % v)
    sfile_new_fd.close()

    col = os.popen("head -1 %s" % (ufile)).read().split()[1]
    ufile_new_fd.write("%s %s\n" % (fea_len, col))
    for i, line in enumerate(file(ufile, "r")):
        if i == 0:
            continue
        if i > fea_len:
            break
        ufile_new_fd.write("%s" % line)
    ufile_new_fd.close()

    col = os.popen("head -1 %s" % (vfile)).read().split()[1]
    vfile_new_fd.write("%s %s\n" % (fea_len, col))
    for i, line in enumerate(file(vfile, "r")):
        if i == 0:
            continue
        if i > fea_len:
            break
        vfile_new_fd.write("%s" % line)
    vfile_new_fd.close()

    return (ufile_new, sfile_new, vfile_new)
    #return (ufile, sfile, vfile)

def transfer_disk(filename, header = True):
    col, row = os.popen("head -1 %s" % (filename)).read().split()
    filename_tmp = '%s_tmp' % filename
    filename_sort = '%s_sort' % filename
    filename_tmp_fd = file(filename_tmp, "w")
    i = 0
    for line in file(filename, "r"):
        if header:
            header = not header
            continue

        datalist = line.strip().split()
        for j in range(len(datalist)):
            filename_tmp_fd.write("%s %s %s\n" % (j, i, datalist[j]))
        i = i + 1

    filename_tmp_fd.close()
    cmd = 'sort -n %s > %s' % (filename_tmp, filename_sort)
    os.system(cmd)

    filename_fd = file(filename, "w")
    filename_fd.write("%s %s\n" % (row, col))
    i = 0
    for line in file(filename_sort, "r"):
        if (i + 1) % int(col) == 0:
            filename_fd.write("%s\n" % line.split()[-1])
        else:
            filename_fd.write("%s " % line.split()[-1])
        i = i + 1

    filename_fd.close()
    remove_file(filename_tmp)
    remove_file(filename_sort)

    return filename

def gen_lg_xinput_file_new(u_file, s_file, header = True):
    transfer_disk(u_file, header)
    row, col = os.popen("head -1 %s" % (u_file)).read().split()

    s_row = os.popen("head -1 %s" % (s_file)).read().split()[0]
    s_matrix = []
    header_flag = header
    for line in file(s_file):
        if header_flag:
            header_flag = not header_flag
            continue
        s_matrix.append(float(line.strip()))

    #print s_row, col
    assert(float(s_row) == float(col))
    uvfile = "%sv" % u_file
    uvfile_fd = file(uvfile, "w")
    uvfile_fd.write("%s %s\n" % (row, col))

    header_flag = header
    for line in file(u_file, "r"):
        if header_flag:
            header_flag = not header_flag
            continue
        rowlist = map(float, line.split())
        for idx, item in enumerate(rowlist):
            if idx == len(rowlist) - 1:
                uvfile_fd.write("%f\n" % (item * float(s_matrix[idx])))
            else:
                uvfile_fd.write("%f " % (item * float(s_matrix[idx])))

    uvfile_fd.close()
    return uvfile

def gen_multi_lg_input_file(data_file, y_file, with_header = True):
    logger.info("gen no weight liblinear lg input: %s %s" % (data_file, y_file))
    output_dir = os.path.dirname(data_file)

    liblinear_input_path = "%s/%s_libin" % (output_dir, os.path.basename(data_file))
    liblinear_input_file = file(liblinear_input_path, "w")

    y_vals = file(y_file).readlines()
    #U matrix
    header = with_header

    i = 0
    for line in file(data_file):
        if header:
            header = not header
            continue

        y = int(float(y_vals[i].strip()))

        i = i + 1
        rowlist = line.split()
        row_str = ' '.join([ '%s:%s' % (j + 1, rowlist[j]) for j in range(len(rowlist)) if float(rowlist[j])>0])

        liblinear_input_file.write('%s %s\n' % (y, row_str))

    liblinear_input_file.close()
    return liblinear_input_path, ""

def gen_lg_input_file(data_file, y_file, with_header = True):
    """ use weight gen lg
    """
    logger.info("gen liblinear lg input: %s %s" % (data_file, y_file))
    output_dir = os.path.dirname(data_file)

    liblinear_input_path = "%s/%s_libin" % (output_dir, os.path.basename(data_file))
    liblinear_input_file = file(liblinear_input_path, "w")
    liblinear_input_wpath = "%s/%s_libin_w" % (output_dir, os.path.basename(data_file))
    liblinear_input_wfile = file(liblinear_input_wpath, "w")

    y_vals = file(y_file).readlines()
    #U matrix
    header = with_header

    #weight_scale = 1
    weight_scale = 100000000

    #row, col = map(int, os.popen("head -1 %s" % (v_file)).read().split())
    liblinear_input_file.write('1\n')
    liblinear_input_wfile.write("0.0000001\n")
    i = 0
    for line in file(data_file):
        if header:
            header = not header
            continue

        y = float(y_vals[i])
        i = i + 1
        rowlist = line.split()
        #feature_no. : 1/0
        row_str = ' '.join([ '%s:%s' % (j + 1, rowlist[j]) for j in range(len(rowlist)) if float(rowlist[j])>0])

        #score >0
        if abs(y) > 1e-9:
            #sample split +
            liblinear_input_file.write('%s %s\n' % (1, row_str))
            liblinear_input_wfile.write("%s\n" % (y * weight_scale))
            #liblinear_input_wfile.write("%s\n" % (1 * weight_scale))

            #sample split -
            if abs(y)<1:
                liblinear_input_file.write('%s %s\n' % (0, row_str))
                liblinear_input_wfile.write("%s\n" % ((1 - y) * weight_scale))
        #score 0
        else:
            liblinear_input_file.write('%s %s\n' % (0, row_str))
            liblinear_input_wfile.write("%s\n" % (1 * weight_scale))

    liblinear_input_file.close()
    liblinear_input_wfile.close()

    return liblinear_input_path, liblinear_input_wpath

#logistic regression
def run_lg_train(input_file, weight_file, with_bias = True):
    output_file = "%s.model" % input_file
    if weight_file:
        weight_para = "-W %s" % weight_file
    else:
        weight_para = ""
    if with_bias:
        lg_cmd = "%s -q -s 0 %s %s %s" % (FLAGS.liblinear_cmd,
                                           weight_para,
                                           input_file,
                                           output_file
                                           )
    else:
        lg_cmd = "%s -q -s 0 -B 1 %s %s %s" % (FLAGS.liblinear_cmd,
                                                weight_para,
                                                input_file,
                                                output_file
                                                )
    logger.info(lg_cmd)
    os.system(lg_cmd)
    return output_file

def load_multi_lg_model(m_file):
    lines = file(m_file).readlines()
    labels = [[int(i) for i in l.strip().split(' ')[1:]] for l in lines if l.startswith('label')][0]
    start_line = [l for l in enumerate(lines) if l[1].startswith('w\n')][0][0]
    args = [[float(f) for f in l[1].strip().split()] for l in enumerate(lines) if l[0]>start_line]
    return dict([(l[1], [a[l[0]] for a in args]) for l in enumerate(labels)])

def load_lg_model(m_file, noweight=False):
    result = {'w' : []}
    lines = file(m_file).readlines()
    read_w = False
    for i in range(0, len(lines)):
        line = lines[i].strip()
        if line == "w":
            read_w = True
            result['w'] = map(float, [l.strip() for l in lines[i+1 : ]])
            break
        else:
            ls = line.split()
            result[ls[0]] = ls[-1]
    return result

def calc_lg_coef_new(output_file,
                 m_file,
                 v_file = "",
                 s_file = "",
                 pname_file = "",
                 svd_trans = True,
                 r_coef = True,
                 bias = True,
                 noweight = False
                 ):
    pattern_names = []
    if pname_file:
        pattern_names = [l.split()[-1] for l in file(pname_file).readlines()]
        pattern_names.append("(Intercept)")

    a = load_lg_model(m_file, noweight)["w"]

    if svd_trans:
        assert(v_file)
        assert(s_file)
        #b = v * 1/s * a
        v_row, v_col = map(int, os.popen("head -1 %s" % (v_file)).read().split())
        v = [map(float, line.split()) for line in file(v_file)][1:]

        #print v_row, len(a)
        if bias:
            assert(v_row == len(a) - 1)
        else:
            assert(v_row == len(a))

        b = [sum([v[j][i] * a[j] for j in range(0, v_row)]) for i in range(0, v_col)]
    else:
        b = a

    beta_file = file(output_file, "w")

    if r_coef:
        beta_file.write("x\n")
        b_rows = ['"input_%s" %s' % (i, b[i]) for i in range(0, len(b))]
        if bias:
            b_rows += ['"(Intercept)" %s' % a[-1]]
        else:
            b_rows += ['"(Intercept)" 0']
        beta_file.write("%s\n" % ("\n".join(b_rows)))
    else:
        beta_file.write("%s 1\n" % len(b))

        if pattern_names:
            beta_file.write("%s\n" % ("\n".join(map(lambda x : '%s %s' % (x[0], x[1]),
                                                zip(b, pattern_names)))))
        else:
            beta_file.write("%s\n" % ("\n".join(map(str, b))))

    beta_file.close()

def calc_lg_coef(output_file,
                 m_file,
                 v_file = "",
                 s_file = "",
                 pname_file = "",
                 svd_trans = True,
                 r_coef = True,
                 noweight = False
                 ):
    """从liblinear的输出 生成统一的coef文件
    TODO:这种格式是为了跟R的输出兼容，以后应该抛弃
    """
    pattern_names = []
    if pname_file:
        pattern_names = [l.split()[-1] for l in file(pname_file).readlines()]
        pattern_names.append("(Intercept)")

    a = load_lg_model(m_file)["w"]

    if svd_trans:
        assert(v_file)
        assert(s_file)
        #b = v * 1/s * a
        v = [map(float, line.split()) for line in file(v_file)][1:]
        v_row, v_col, v = trans_matrix(v)

        s = [1.0 / float(x.strip()) for x in file(s_file)][1:]
        assert(len(s) == v_col)
        b = [sum([v[i][j] * s[j] * a[j] for j in range(0, len(s))]) for i in range(0, v_row)]
    else:
        b = a

    beta_file = file(output_file, "w")

    if r_coef:
        beta_file.write("x\n")
        b_rows = ['"input_%s" %s' % (i, b[i]) for i in range(0, len(b) - 1) ]
        b_rows += ['"(Intercept)" %s' % b[-1]]
        beta_file.write("%s\n" % ("\n".join(b_rows)))
    else:
        beta_file.write("%s 1\n" % len(b))

        if pattern_names:
            beta_file.write("%s\n" % ("\n".join(map(lambda x : '%s %s' % (x[0], x[1]),
                                                zip(b, pattern_names)))))
        else:
            beta_file.write("%s\n" % ("\n".join(map(str, b))))

    beta_file.close()

def svd_regression(input_file, output_file):
    logger.info("svd_regression %s %s" % (input_file, output_file))

    svdin_file_path = gen_svd_input(input_file, add_1_end = False)

    y_file_path = "%s/%s_result" % (os.path.dirname(input_file), os.path.basename(input_file))

    gen_y_file(input_file, y_file_path, with_header = True, y_column = -1)

    u_file, s_file, v_file = run_svd(svdin_file_path)
    #compute u * sT
    x_file = gen_lg_xinput_file_new(u_file, s_file)

    lg_input, weight_input = gen_lg_input_file(x_file,
                                               y_file_path,
                                               with_header = True #svd output U with header
                                               )

    mfile = run_lg_train(lg_input,
                         weight_input,
                         with_bias = False # bias 已经包含在svd输出的U中
                         )

    calc_lg_coef_new(output_file, mfile, v_file = v_file, s_file = s_file, svd_trans = True, bias = True)

def lg_regression(input_file, output_file, noweight = False):
    """liblinear logistic regression"""

    logger.info("lg_regression %s %s" % (input_file, output_file))

    #import pdb; pdb.set_trace()
    x_file_path, y_file_path = gen_x_y_file(input_file)

    if noweight:
        lg_input, weight_input = gen_multi_lg_input_file(x_file_path,
                                               y_file_path,
                                               with_header = False
                                               )
    else:
        lg_input, weight_input = gen_lg_input_file(x_file_path,
                                               y_file_path,
                                               with_header = False
                                               )

    mfile = run_lg_train(lg_input,
                         weight_input,
                         with_bias = False
                         )

    r_coef_file = "%svar.lg.coef.txt" % (input_file.rsplit("data.txt", 1)[0])

    calc_lg_coef(output_file, mfile, svd_trans = False, noweight = noweight)
