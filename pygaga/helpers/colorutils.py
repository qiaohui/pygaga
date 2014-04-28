from collections import namedtuple
from math import sqrt
import random
import colorsys
from PIL import Image, ImageDraw
from colorific import norm_color, rgb_to_hex, hex_to_rgb

Point = namedtuple('Point', ('coords', 'n', 'ct'))
Cluster = namedtuple('Cluster', ('points', 'center', 'n'))

def get_points(img):
    points = []
    w, h = img.size
    for count, color in img.getcolors(w * h):
        points.append(Point(color, 3, count))
    return points

rtoh = lambda rgb: '#%s' % ''.join(('%02x' % p for p in rgb))

def colorz(filename, n=3, manual_crop_percent=None):
    img = Image.open(filename)
    if manual_crop_percent:
        img = img.crop((int(img.size[0]*manual_crop_percent[0]),
            int(img.size[1]*manual_crop_percent[1]),
            int(img.size[0]*manual_crop_percent[2]),
            int(img.size[1]*manual_crop_percent[3])))
    img.thumbnail((200, 200))
    w, h = img.size

    points = get_points(img)
    clusters = kmeans(points, n, 1)
    rgbs = [map(int, c.center.coords) for c in clusters]
    return map(rtoh, rgbs)

def euclidean(p1, p2):
    return sqrt(sum([
        (p1.coords[i] - p2.coords[i]) ** 2 for i in range(p1.n)
    ]))

def calculate_center(points, n):
    vals = [0.0 for i in range(n)]
    plen = 0
    for p in points:
        plen += p.ct
        for i in range(n):
            vals[i] += (p.coords[i] * p.ct)
    return Point([(v / plen) for v in vals], n, 1)

def kmeans(points, k, min_diff):
    clusters = [Cluster([p], p, p.n) for p in random.sample(points, k)]

    while 1:
        plists = [[] for i in range(k)]

        for p in points:
            smallest_distance = float('Inf')
            for i in range(k):
                distance = euclidean(p, clusters[i].center)
                if distance < smallest_distance:
                    smallest_distance = distance
                    idx = i
            plists[idx].append(p)

        diff = 0
        for i in range(k):
            old = clusters[i]
            center = calculate_center(plists[i], old.n)
            new = Cluster(plists[i], center, old.n)
            clusters[i] = new
            diff = max(diff, euclidean(old.center, new.center))

        if diff < min_diff:
            break

    return clusters

def colors_as_image(colors):
    "Save palette as a PNG with labeled, colored blocks"
    colors = [hex_to_rgb("#%s" % c) for c in colors]
    size = (80 * len(colors), 80)
    im = Image.new('RGB', size)
    draw = ImageDraw.Draw(im)
    for i, c in enumerate(colors):
        v = colorsys.rgb_to_hsv(*norm_color(c))[2]
        (x1, y1) = (i * 80, 0)
        (x2, y2) = ((i + 1) * 80 - 1, 79)
        draw.rectangle([(x1, y1), (x2, y2)], fill=c)
        if v < 0.6:
            # white with shadow
            draw.text((x1 + 4, y1 + 4), rgb_to_hex(c), (90, 90, 90))
            draw.text((x1 + 3, y1 + 3), rgb_to_hex(c))
        else:
            # dark with bright "shadow"
            draw.text((x1 + 4, y1 + 4), rgb_to_hex(c), (230, 230, 230))
            draw.text((x1 + 3, y1 + 3), rgb_to_hex(c), (0, 0, 0))
    return im

if __name__ ==  "__main__":
    import gflags
    from pygaga.helpers.logger import log_init
    FLAGS = gflags.FLAGS

    gflags.DEFINE_string('filename', '', "file name")
    gflags.DEFINE_integer('n', 3, "how many k-means")

    FLAGS.stderr = True
    FLAGS.verbose = "info"
    FLAGS.color = True
    log_init()
    print colorz(FLAGS.filename, FLAGS.n)

