# -*- coding: utf-8 -*-
import qrcode
from PIL import Image
from pyzbar.pyzbar import ZBarSymbol, decode
import math
import base64
import numpy as np
import cv2

InputfilePath = './sample/lenna.jpg'
outputQrPath  = './QRimage/out'
outputfilePath = 'out.jpg'
baseimagePath = './sample/longcat.png'
inputBaseimagePath = 'stegano_longcat.png'

def makeqr(binary):
    qr = qrcode.QRCode(
        version=4,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=2,
        border=4
    )
    qr.add_data(binary)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img.resize(img.size)

def join_file(fileList, filePath):
    with open(filePath, 'wb') as saveFile:
        for f in fileList:
            saveFile.write(f)
            saveFile.flush()
        saveFile.close()

def openAndDecode(img):
    data = decode(img, symbols=[ZBarSymbol.QRCODE])
    data.sort(key=lambda x: (x[2][1], x[2][0]))
    decoded = [base64.b64decode(i[0] + b"="*((4 - len(i[0])%4))) for i in data]
    return decoded

def chunkbinary(path, chunkLength) :
    readLength, count = 0, 1
    chunkLength -= chunkLength % 4
    f = open(path, 'rb')
    data = base64.b64encode(f.read())
    countLength = len(data)
    arr = []
    while readLength < countLength:
        arr.append(data[readLength:chunkLength*count])
        readLength += chunkLength
        count += 1
    return arr

def makeQRimage(qrimageList, basesize):
    outputimagelist = []
    expect_qr = (math.floor(basesize[0]/qrimageList[0].width)*math.floor(basesize[1]/qrimageList[0].height))
    print('MAX QR PER LAYER :', expect_qr)
    print('MAX: ', ((76*expect_qr*3)*7)/1000, 'KB')
    offset = 0
    while offset < len(qrimageList):
        dst = Image.new('1', basesize, 'white')
        coordinate_width, coordinate_height = 0, 0
        for i in range(expect_qr if len(qrimageList) - offset > expect_qr else len(qrimageList) - offset):
            if coordinate_width + qrimageList[offset+i].height >= basesize[0]: 
                coordinate_width = 0
                coordinate_height += qrimageList[offset+i].height
            dst.paste(qrimageList[offset+i], (coordinate_width, coordinate_height))
            coordinate_width += qrimageList[offset+i].width
        outputimagelist.append(dst)
        offset += expect_qr
    return outputimagelist

def steganoDecode(img, layer):
    layer = 21
    decodedImageList = []
    imgArray = np.array(img)
    for i in range(21):
        hash = (imgArray[:,:,(i%3)] % pow(2, math.ceil(layer/3)))
        arr = (hash >> int(i/3)) % 2
        decodedImageList.append(Image.fromarray(arr.astype(np.bool_)))
    return decodedImageList

def setupBaseImage(img, layer):
    numpyImg = np.array(img)
    for px in numpyImg[:,:,0:3]:
        px -= (px % pow(2, math.ceil(layer/3)))
    return Image.fromarray(numpyImg)

def appendStegano(baseImg, steganoList):
    baseArray = np.array(baseImg)
    if type(steganoList) != list: steganoList = [steganoList]
    for i in range(len(steganoList)) :
        masqimg = steganoList[i].convert('1')
        baseArray[:,:,(i%3)] += np.array(masqimg).astype(np.uint8) * pow(2, int(i/3))
    return Image.fromarray(baseArray)

if __name__ == '__main__' :
    qrimage = [makeqr(i) for i in chunkbinary(InputfilePath, 76)]
    masqimg = makeQRimage(qrimage, Image.open(baseimagePath).size) #list of qr sheet
    layer = len(masqimg)
    print('LAYER: ', layer)
    base = setupBaseImage(Image.open(baseimagePath), layer)
    appendStegano(base, masqimg).save(inputBaseimagePath)
    for i in range(layer):
        masqimg[i].save(outputQrPath+str(i)+'.png')
    out = Image.open(inputBaseimagePath)
    steganoList = [i for i in steganoDecode(out, layer)]
    decodedBinaly = []
    for i in range(layer):
        decodedBinaly.extend(openAndDecode(steganoList[i]))
    join_file(decodedBinaly, outputfilePath)