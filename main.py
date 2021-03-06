import numpy as np
import cv2

#cap = cv2.VideoCapture('D:\\Work_Documents\\sandbox\\OpenCV\\with_EEN\\viaVLC\\EN-CDUM-002a+2016-08-29+14-38-40.mp4') #Open video file
cap = cv2.VideoCapture('C:\\Users\\kurok\\Desktop\\prog\\test2.mp4')
#cap = cv2.VideoCapture('http://127.0.0.1:8080')

fps = 15 #int(cap.get(5)+4)
print ('Current FPS is ' + str(fps))
#cv2.ocl.setUseOpenCL(False)
fgbg = cv2.createBackgroundSubtractorKNN(detectShadows = True) #Create the background substractor

# initialize var and windows
itr = 0
crossed = 0
font = cv2.FONT_HERSHEY_SIMPLEX
old_center = np.empty((0,2), float)
'''
cv2.namedWindow("Frame", cv2.WINDOW_KEEPRATIO | cv2.WINDOW_NORMAL)
cv2.namedWindow("Background Substraction", cv2.WINDOW_KEEPRATIO | cv2.WINDOW_NORMAL)
cv2.namedWindow("Contours", cv2.WINDOW_KEEPRATIO | cv2.WINDOW_NORMAL)
'''

# define functions
def padding_position(x, y, w, h, p):
    return x - p, y - p, w + p * 2, h + p * 2

# find a nearest neighbour point
def serchNN(p0, ps):
    L = np.array([])
    for i in range(ps.shape[0]):
        L = np.append(L,np.linalg.norm(ps[i]-p0))
    return ps[np.argmin(L)]

# check intersect 2 lines
def isIntersect(ap1, ap2, bp1, bp2):
    calc1 = ((ap1[0] - ap2[0]) * (bp1[1] - ap1[1]) + (ap1[1] - ap2[1]) * (ap1[0] - bp1[0])) * ((ap1[0] - ap2[0]) * (bp2[1] - ap1[1]) + (ap1[1] - ap2[1]) * (ap1[0] - bp2[0]))
    calc2 = ((bp1[0] - bp2[0]) * (ap1[1] - bp1[1]) + (bp1[1] - bp2[1]) * (bp1[0] - ap1[0])) * ((bp1[0] - bp2[0]) * (ap2[1] - bp1[1]) + (bp1[1] - bp2[1]) * (bp1[0] - ap2[0]))
    if (calc1 < 0):
        if (calc2 < 0):
            return True
    return False

# apply convexHull to the contour
def convHull(cnt):
    epsilon = 0.1*cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, epsilon, True)
    hull = cv2.convexHull(cnt, returnPoints = True)
    return hull

# detect a centroid from a coutour
def centroidPL(cnt):
    M = cv2.moments(cnt)
    cx = int(M['m10']/M['m00'])
    cy = int(M['m01']/M['m00'])
    return cx,cy

# display 1st frame and set counting line
ret, img = cap.read()
img = cv2.putText(img, 'Please draw a line with drug the mouse.', (int(img.shape[1]/2-300), int(img.shape[0]/2)), font, 1, (0,0,255), 2, cv2.LINE_AA)
img = cv2.putText(img, 'Finish the draw, press ESC. \n Retry, press "r".', (int(img.shape[1]/2-300), int(img.shape[0]/2+40)), font, 1, (0,0,255), 2, cv2.LINE_AA)
img = cv2.putText(img, 'Retry, press "r".', (int(img.shape[1]/2-300), int(img.shape[0]/2+80)), font, 1, (0,0,255), 2, cv2.LINE_AA)
img = cv2.resize(img, (int(img.shape[1]/2), int(img.shape[0]/2)))
imgr = img.copy()
sx,sy = -1,-1
ex,ey = -1,-1

def draw_line(event,x,y,flags,param):
    global sx,sy,ex,ey

    if event == cv2.EVENT_LBUTTONDOWN:
        sx,sy = x,y
        
    elif event == cv2.EVENT_LBUTTONUP:
        cv2.line(img,(sx,sy),(x,y),(255,0,0), 2)
        ex,ey = x,y
               

cv2.namedWindow('Draw_Line')
#cv2.setMouseCallback('Draw_Line',draw_line)

sx  = int(img.shape[1]/2)
sy = 0
ex = int(img.shape[1]/2)
ey = int(img.shape[0])


while(1):
    cv2.imshow('Draw_Line',img)
    k = cv2.waitKey(20) & 0xFF
    if k == 27:
        break
    elif k == ord('r'):
        img = imgr.copy()
        continue

cv2.destroyAllWindows()

# initialize line
lp0 = (sx, sy)
lp1 = (ex, ey)
nlp0 = np.array([lp0[0], lp0[1]], float)
nlp1 = np.array([lp1[0], lp1[1]], float)

while(cap.isOpened()):
    try:
        ret, o_frame = cap.read() #read a frame
        frame = cv2.resize(o_frame, (int(o_frame.shape[1]/2), int(o_frame.shape[0]/2)))

        #Use the substractor
        fgmask = fgbg.apply(frame) 
        fgmask_o = fgmask.copy()

        fgmask = cv2.threshold(fgmask, 244, 255, cv2.THRESH_BINARY)[1]
        kernel = np.ones((5,5), np.uint8)
#        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_CLOSE, kernel)
        fgmask = cv2.dilate(fgmask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3)), iterations = 2)

        im2, contours, hierarchy = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # initialize var iteration
        new_center = np.empty((0,2), float)

        for c in contours:

            if (itr % fps == 0):
                continue

            # calc the area
            cArea = cv2.contourArea(c)
            if cArea < 300: # if 1280x960 set to 50000, 640x480 set to 12500
                continue

            # apply the convex hull 
            c = convHull(c)

            # rectangle area
            x, y, w, h = cv2.boundingRect(c)
            x, y, w, h = padding_position(x, y, w, h, 5)

            # center point
            cx, cy = centroidPL(c)
            new_point = np.array([cx, cy], float)
            new_center = np.append(new_center, np.array([[cx, cy]]), axis=0)

            if (old_center.size > 1):
                #print cArea and new center point
                print ('Loop: ' + str(itr) + '   Coutours #: ' + str(len(contours)))
                print ('New Center :' + str(cx) + ',' + str(cy))
                #print 'New Center :' + str(new_center)

                # calicurate nearest old center point
                old_point_t = serchNN(new_point, old_center)

                # check the old center point in the counding box
                if (cv2.pointPolygonTest(c, (old_point_t[0], old_point_t[1]), True) > 0):
                    old_point = old_point_t
                    print ('Old Center :' + str(int(old_point[0])) + ',' + str(int(old_point[1])))

                    # put line between old_center to new_center
                    cv2.line(frame, (int(old_point[0]), int(old_point[1])), (cx, cy), (0,0,255), 2)

                    # cross line check
                    if (isIntersect(nlp0, nlp1, old_point, new_point)):
                        print ('Crossing!')
                        if(nlp0[0] < old_point[0]):
                            crossed += 1
                        else:
                            crossed -= 1


            # put floating text
            cv2.putText(frame, 'CA:' + str(cArea)[0:-2] , (x+10, y+20), font, 0.5, (255,255,255), 1, cv2.LINE_AA)

            # draw center
            cv2.circle(frame,(cx,cy),5,(0,0,255),-1)

            # draw rectangle or contour
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)  #rectangle contour
#            cv2.drawContours(frame, [c], 0, (0,255,0), 2)
#            cv2.polylines(frame, [c], True, (0,255,0), 2)

        # put fixed text, line and show images
        cv2.putText(frame, 'Crossing:' + str(crossed), (int(o_frame.shape[1]/4), 30), font, 1, (255,255,255), 1, cv2.LINE_AA)
        cv2.line(frame, (lp0), (lp1), (255,0,0), 2)
        cv2.imshow('Frame',frame)
        cv2.imshow('Background Substraction',fgmask_o)
        cv2.imshow('Contours',fgmask)

        # increase var number and renew center array
        old_center = new_center
        itr += 1

    except:
        #if there are no more frames to show...
        print('EOF')
        import traceback
        traceback.print_exc()
        break

    #Abort and exit with 'Q' or ESC
    k = cv2.waitKey(30) & 0xff
    if k == 27:
        break

cap.release() #release video file
cv2.destroyAllWindows() #close all openCV windows