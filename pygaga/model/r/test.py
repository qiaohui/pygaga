from jinja2 import Template 

def split_column():
	template = Template(file("split_columns.r").read())
	print template.render({ 'row_file':'row_file.txt',
							'split_count':12,
							'filenames':["1.txt", "2.txt", "3.txt"]
							})

def select_feature():
	template = Template(file("select_feature.r").read())
	print template.render({ 'feature_file':'feature_file.txt',
							'i':2,
							'column_filenames':[
								["1.txt", "2.txt", "3.txt"],
								["11.txt", "12.txt", "13.txt"],
								["21.txt", "22.txt", "23.txt"],
								["31.txt", "32.txt", "33.txt"],
								]							
							})

def merge_feature():
	template = Template(file("merge_feature.r").read())
	print template.render({ 'select_feature_file':'select_feature_file.txt',
							'column_blocks':range(3),
							'feature_files':[
								"1.txt", "2.txt", "3.txt"
								]							
							})

def strip_data_file():
	template = Template(file("generate_strip_data.r").read())
	print template.render({ 'features':'y ~ x1+x2',
							'strip_data_file':'strip.txt',
							'files':[
								"1.txt", "2.txt", "3.txt"
								]							
							})
														
#split_column()
#select_feature()
#merge_feature()	
strip_data_file()