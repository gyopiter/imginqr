    # -*- coding: utf-8 -*-

import os
import qrcode
from PIL import Image
from pyzbar.pyzbar import ZBarSymbol, decode
import math
import sys
import base64
import numpy as np
import cv2

InputfilePath = './sample/kenpo.html'
outputQrPath  = './QRimage/test'
outputfilePath = 'out.html'
baseimagePath = './sample/InputBaseImage.jpg'
inputBaseimagePath = 'outputBaseImage.png'

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
    while (chunkLength % 4 != 0) : chunkLength -= 1
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

#===実装
def steganoDecode(img, layer):
    decodedImageList = []
    imgArray = np.array(img)
    for i in range(layer):
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
#===

def playMedia(openPath):
    cap = cv2.VideoCapture(openPath)
    if (cap.isOpened() == False):
        print("Error opening video  file")
    while(cap.isOpened()):
        ret, frame = cap.read()
        if ret == True:
            cv2.imshow('Frame', frame)
            if cv2.waitKey(25) & 0xFF == ord('q'): break
        else: break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__' :
    '''
    qrimage = [makeqr(i) for i in chunkbinary(InputfilePath, 624)]
    #全てのQR画像データを一つのイメージに表すための台紙のサイズを設定
    base_size = (2508,3541)

    qroutput = makeQRimage(qrimage, base_size)
    for i in range(len(qroutput))
        qroutput[i].save(outputQrPath+str(i)+'.jpg')
    print('ENCODE:', len(qrimage))
    print("decode...")
    decoded = []
    for i in range(len(qroutput)): 
        img = Image.open(outputQrPath+str(i)+'.jpg')
        decoded.extend(openAndDecode(img))
        
    print('DECODED:', len(decoded))
    join_file(decoded, outputfilePath)
    '''

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
    #Image.open(outputfilePath).show()
    #playMedia(outputfilePath)