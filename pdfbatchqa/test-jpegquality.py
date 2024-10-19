import io
import pprint
pp = pprint.PrettyPrinter(indent=4)
from PIL import Image

def get_jpg_quality(image) -> int:
    """
    Implement quality computation following ImageMagick heuristic algorithm:
    https://github.com/ImageMagick/ImageMagick/blob/7.1.0-57/coders/jpeg.c#L782
    Usage:
    ```
    pim = Img.open(...)
    quality = get_jpg_quality(pim)
    ```
    See also https://stackoverflow.com/questions/4354543/
    """

    NUM_QUANT_TBLS = 4
    DCTSIZE2 =  64

    _HASH_2 = [  1020, 1015,  932,  848,  780,  735,  702,  679,  660,  645,
                632,  623,  613,  607,  600,  594,  589,  585,  581,  571,
                555,  542,  529,  514,  494,  474,  457,  439,  424,  410,
                397,  386,  373,  364,  351,  341,  334,  324,  317,  309,
                299,  294,  287,  279,  274,  267,  262,  257,  251,  247,
                243,  237,  232,  227,  222,  217,  213,  207,  202,  198,
                192,  188,  183,  177,  173,  168,  163,  157,  153,  148,
                143,  139,  132,  128,  125,  119,  115,  108,  104,   99,
                94,   90,   84,   79,   74,   70,   64,   59,   55,   49,
                45,   40,   34,   30,   25,   20,   15,   11,    6,    4,
                0 ]
    _SUMS_2 = [  32640, 32635, 32266, 31495, 30665, 29804, 29146, 28599, 28104,
                27670, 27225, 26725, 26210, 25716, 25240, 24789, 24373, 23946,
                23572, 22846, 21801, 20842, 19949, 19121, 18386, 17651, 16998,
                16349, 15800, 15247, 14783, 14321, 13859, 13535, 13081, 12702,
                12423, 12056, 11779, 11513, 11135, 10955, 10676, 10392, 10208,
                9928,  9747,  9564,  9369,  9193,  9017,  8822,  8639,  8458,
                8270,  8084,  7896,  7710,  7527,  7347,  7156,  6977,  6788,
                6607,  6422,  6236,  6054,  5867,  5684,  5495,  5305,  5128,
                4945,  4751,  4638,  4442,  4248,  4065,  3888,  3698,  3509,
                3326,  3139,  2957,  2775,  2586,  2405,  2216,  2037,  1846,
                1666,  1483,  1297,  1109,   927,   735,   554,   375,   201,
                128,     0 ]
    _HASH_1 = [    510,  505,  422,  380,  355,  338,  326,  318,  311,  305,
                300,  297,  293,  291,  288,  286,  284,  283,  281,  280,
                279,  278,  277,  273,  262,  251,  243,  233,  225,  218,
                211,  205,  198,  193,  186,  181,  177,  172,  168,  164,
                158,  156,  152,  148,  145,  142,  139,  136,  133,  131,
                129,  126,  123,  120,  118,  115,  113,  110,  107,  105,
                102,  100,   97,   94,   92,   89,   87,   83,   81,   79,
                76,   74,   70,   68,   66,   63,   61,   57,   55,   52,
                50,   48,   44,   42,   39,   37,   34,   31,   29,   26,
                24,   21,   18,   16,   13,   11,    8,    6,    3,    2,
                    0 ]
    _SUMS_1 = [
                16320, 16315, 15946, 15277, 14655, 14073, 13623, 13230, 12859,
                12560, 12240, 11861, 11456, 11081, 10714, 10360, 10027,  9679,
                9368,  9056,  8680,  8331,  7995,  7668,  7376,  7084,  6823,
                6562,  6345,  6125,  5939,  5756,  5571,  5421,  5240,  5086,
                4976,  4829,  4719,  4616,  4463,  4393,  4280,  4166,  4092,
                3980,  3909,  3835,  3755,  3688,  3621,  3541,  3467,  3396,
                3323,  3247,  3170,  3096,  3021,  2952,  2874,  2804,  2727,
                2657,  2583,  2509,  2437,  2362,  2290,  2211,  2136,  2068,
                1996,  1915,  1858,  1773,  1692,  1620,  1552,  1477,  1398,
                1326,  1251,  1179,  1109,  1031,   961,   884,   814,   736,
                    667,   592,   518,   441,   369,   292,   221,   151,    86,
                    64,     0 ]

    qsum = 0
    qdict = image.quantization
    for i, qtable in qdict.items():
        qsum += sum(qtable)
    
    print("qsum: " + str(qsum))

    print("qdict length: " + str(len(qdict)))
    if len(qdict) >= 1:
        qvalue = qdict[0][2]+qdict[0][53]
        print("qvalue: " + str(qvalue))
        hash, sums = _HASH_1, _SUMS_1
        if len(qdict) >= 2:
            qvalue += qdict[1][0]+qdict[1][-1]
            hash, sums = _HASH_2, _SUMS_2
            print("qvalue: " + str(qvalue))
        for i in range(100):
            print("i, qvalue, hash, qsum, sums: ", str(i), str(qvalue), str(hash[i]), str(qsum), str(sums[i]))
            if ((qvalue < hash[i]) and (qsum < sums[i])):
                continue
            if (((qvalue <= hash[i]) and (qsum <= sums[i])) or (i >= 1)):
                return i+1
            break
    return -1


#myJPEG = "/home/johan/test/BKT-ecur/images/-000.jpg"
#myJPEG = "/home/johan/test/kort004mult/300ppi-50/images/crap-008.jpg"
myJPEGs = ["/home/johan/test/wizard-50.jpg",
           "/home/johan/test/wizard-60.jpg",
           "/home/johan/test/wizard-80.jpg",
           "/home/johan/test/BKT-ecur/images/-000.jpg",
           "/home/johan/test/kort004mult/300ppi-50/images/crap-008.jpg",
           "/home/johan/test/BKT-ecur/images/-000.jpg",
           "/home/johan/test/wizard-20.jpg",
           "/home/johan/test/wizard-15.jpg",
           "/home/johan/test/wizard-10.jpg",
           "/home/johan/test/260761857-bdf17e14-c697-4f4a-b6d5-e3067e0afc08.jpeg"]

for myJPEG in myJPEGs:
    with open(myJPEG, 'rb') as fIn:
            print(myJPEG)
            im = Image.open(fIn)
            im.load()
            pprint.pp(im.quantization)
            quality = get_jpg_quality(im)
            print(str(quality))
            # Get quantization table
            #qTable = im.quantization
            #print(qTable)

