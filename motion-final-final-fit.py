import numpy as np
import cv2 as cv
import imutils
import time
from matplotlib import pyplot as plt
import glob

def fit(x, y): #Curve Fitting Straight line

    xbar = sum(x)/len(x)
    ybar = sum(y)/len(y)
    n = len(x) # or len(y)

    numer = sum([xi*yi for xi,yi in zip(x, y)]) - n * xbar * ybar
    denum = sum([xi**2 for xi in x]) - n * xbar**2

    a = numer / denum
    b = ybar - a * xbar
    return a, b



def boundary_removal(img): #Remove edges from the boundary
    for i in range (1,13):
        img[:,-i]=img[:,-15]

        
    for i in range (0,12):
        img[:,i]=img[:,15]


    for i in range (0,12):
        img[i,:]=img[15,:]
    
    return img

def estimate_plane(a, b, c):
    """Estimate the parameters of the plane passing by three points.
    Returns:center(float): The center point of the three input points.
    normal(float): The normal to the plane."""
    center = (a + b + c) / 3
    normal = np.cross(b - a, c - a)
    assert(np.isclose(np.dot(b - a, normal), np.dot(c - a, normal)))
    return center, normal

def rotation_matrix_from_vectors(vec1, vec2):
    """ Find the rotation matrix that aligns vec1 to vec2
    :param vec1: A 3d "source" vector
    :param vec2: A 3d "destination" vector
    :return mat: A transform matrix (3x3) which when applied to vec1, aligns it with vec2.
    """
    a, b = (vec1 / np.linalg.norm(vec1)).reshape(3), (vec2 / np.linalg.norm(vec2)).reshape(3)
    v = np.cross(a, b)
    c = np.dot(a, b)
    s = np.linalg.norm(v)
    kmat = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    rotation_matrix = np.eye(3) + kmat + kmat.dot(kmat) * ((1 - c) / (s ** 2))
    return rotation_matrix

filenames=glob.glob("C:/Users/User/Desktop/Test/*.jpg")

last_last_straightline_params = None
last_straightline_params = None
image_counter = 0



for file in filenames:
    ts=time.time()
    image_counter +=1
    if image_counter == 1:
        img = cv.imread(file,0)
        img_height=img.shape[0] #1080
        img_width=img.shape[1] #1920

        #HFOV=Horizontal Field of View
        #HFOV_GoPro=170° ; Raspberry=62.2°
        HFOV=62.2
        #F(pixels)=F(mm)*ImageWidth (pixel)/SensorWidth(mm)
        #focal_pixel = (image_width_in_pixels * 0.5) / tan(HFOV * 0.5 * PI/180)
        focal_length_pixel = (img_width * 0.5) / np.tan(HFOV * 0.5 * np.pi/180)
        #Focal length milimiters 1.7 mm lens GoPro. Raspberry 3.04 mm
        focal_length_mm=3.04
        print('Focal length in pixels',focal_length_pixel,'\n')
  
        img = boundary_removal(img)

        x_position = []
        y_position = []
        for i in range (0,len(img[0,:]),5):
            for j in range (0,len(img[:,0]),5):
                if img[j,i]==0:
                    x_position.append(i)
                    y_position.append(j)
                    break
        a, b = fit(x_position, y_position)
        #print ("a value first image:",a,,'\n',"b value first image:",b,'\n')
        angle_a=np.arctan(a)
        last_last_angle=angle_a
        last_last_b=b

        #Compensate Movement
        img_reference=img
        reference_angle=angle_a
        reference_b=b


        #Plane1
        p=x_position[int(len(x_position)/2)]
        q=y_position[int(len(y_position)/2)]
        #Threshold values
        t_x=200
        t_y=100
        altitude=300 #80 meters high = 80000 mm
        if p>t_x and q>t_y:
            m=np.array([p,q+50,altitude*focal_length_pixel/focal_length_mm])
            n=np.array([p+100,q+100,altitude*focal_length_pixel/focal_length_mm])
            l=np.array([p-100,img_height,altitude*focal_length_pixel/focal_length_mm])
        else:
            m=np.array([p+t_x,q+t_y+50,altitude*focal_length_pixel/focal_length_mm])
            n=np.array([p+t_x+100,q+t_y+100,altitude*focal_length_pixel/focal_length_mm])
            l=np.array([p+t_x-100,img_height,altitude*focal_length_pixel/focal_length_mm])

        center1,vec1=estimate_plane(m, n, l)
        #print(center1,vec1,'\n')



    elif image_counter == 2:
        img = cv.imread(file,0)
        img = boundary_removal(img)

        x_position = []
        y_position = []
        for i in range (0,len(img[0,:]),5):
            for j in range (0,len(img[:,0]),5):
                if img[j,i]==0:
                    x_position.append(i)
                    y_position.append(j)
                    break
        a, b = fit(x_position, y_position)
        #print (a,b,'\n')
        angle_a=np.arctan(a)
        last_angle=angle_a
        last_b=b
        theta_inc=last_angle-last_last_angle
        #print (theta_inc,'\n')
        b_inc=last_b-last_last_b

        #Compensate Movement
        angle_2=angle_a
        angle_compensate_rad=angle_2-reference_angle
        angle_compensate_degrees=np.rad2deg(angle_compensate_rad)
        #print("Roll angle rad:",angle_compensate_rad,'\n')
        #print("Roll angle degrees:",angle_compensate,'\n')
        rotate_image=img
        allign_image_roll=imutils.rotate(rotate_image,angle_compensate_degrees)
        
        b_2=b
        b_compensate=b_2-reference_b
        #print("b translation:",b_compensate,'\n')
        allign_image_pitch_roll=imutils.translate(allign_image_roll,0,b_compensate)

        b_half=reference_b-img_height/2 #540 half height size resolution
        b_half_angle=np.arctan(b_half/focal_length_pixel) #516 pixels focal lenght Raspberry Pi camera V2 (using calibation)
        b_total=b_half+b_compensate
        b_total_angle=np.arctan(b_total/focal_length_pixel)
        pitch_angle_rad=np.arctan(b_total_angle-b_half_angle)
        pitch_angle_degrees=np.rad2deg(pitch_angle_rad)
        #print("Pitch angle rad: ",pitch_angle_rad,'\n')
        #print("Pitch angle degrees: ",pitch_angle_degrees,'\n')


        #Plane2
        p=x_position[int(len(x_position)/2)]
        q=y_position[int(len(y_position)/2)]
        #Threshold values
        t_x=200
        t_y=100
        altitude=300 #80 meters high = 80000 mm
        if p>t_x and q>t_y:
            m=np.array([p,q+50,altitude*focal_length_pixel/focal_length_mm])
            n=np.array([p+100,q+100,altitude*focal_length_pixel/focal_length_mm])
            l=np.array([p-100,img_height,altitude*focal_length_pixel/focal_length_mm])
        else:
            m=np.array([p+t_x,q+t_y+50,altitude*focal_length_pixel/focal_length_mm])
            n=np.array([p+t_x+100,q+t_y+100,altitude*focal_length_pixel/focal_length_mm])
            l=np.array([p+t_x-100,img_height,altitude*focal_length_pixel/focal_length_mm])

        center2,vec2=estimate_plane(m, n, l)
        rotation_matrix=rotation_matrix_from_vectors(vec2, vec1)
        
        #Plane Results
        theta_x=np.arctan2(rotation_matrix[2,1],rotation_matrix[2,2])
        #print('Theta x rad: ',theta_x)
        theta_y=np.arctan2(-rotation_matrix[2,0],np.sqrt((rotation_matrix[2,1])**2+(rotation_matrix[2,2])**2))
        #print('Theta y rad: ',theta_y)
        theta_z=np.arctan2(rotation_matrix[1,0],rotation_matrix[0,0])
        #print('Theta z rad: ',theta_z,'\n')


    elif image_counter > 2:
        img = cv.imread(file,0)
        img = boundary_removal(img) 
              
        theta_pred=theta_inc+last_angle
        b_pred=last_b+b_inc
        a_p=np.tan(theta_pred)
        b_p=b_pred
        #print (a_p,b_p,'\n')

        last_last_angle=last_angle
        last_last_b=last_b

        

        x_position_predict = [i for i in range(0,len(img[0,:]),5)]
        y_position_predict =[]
        for x in x_position_predict:
            y=a_p*x +b_p
            y_position_predict.append(y)

            

        x_position = x_position_predict 
        y_position = []
        for i,j in zip(x_position,y_position_predict):
            j=int(j)
            if img[j,i] == 0: 
                while (img[j,i] == 0):              
                    j -=1 
                y_position.append(j)
            else:
                while (img[j,i] == 127):              
                    j +=1 
                y_position.append(j)



        a, b = fit(x_position, y_position)
        #print ("a value third image:",a,"b value third image:",b,'\n')
        x_line = np.arange(min(x_position), max(x_position), 1)
        y_line=a*x_line +b
        angle_a=np.arctan(a)
        last_angle=angle_a
        last_b=b
        theta_inc=last_angle-last_last_angle
        b_inc=last_b-last_last_b


        #Compensate Movement
        angle_mov=angle_a
        angle_compensate_rad=angle_mov-reference_angle
        angle_compensate_degrees=np.rad2deg(angle_compensate_rad)
        print("Roll angle rad:",angle_compensate_rad,'\n')
        #print("Roll angle degrees:",angle_compensate,'\n')
        rotate_image=img
        allign_image_roll=imutils.rotate(rotate_image,angle_compensate_degrees)

        b_mov=b
        b_compensate=b_mov-reference_b
        #print("b translation:",b_compensate,'\n')
        allign_image_pitch_roll=imutils.translate(allign_image_roll,0,b_compensate)
        
        b_half=reference_b-img_height/2 #img_height/2=540 half height size resolution
        b_half_angle=np.arctan(b_half/focal_length_pixel) #focal_length_pixel=516 pixels focal lenght Raspberry Pi camera V2 (using calibation)
        b_total=b_half+b_compensate
        b_total_angle=np.arctan(b_total/focal_length_pixel)
        pitch_angle_rad=np.arctan(b_total_angle-b_half_angle)
        pitch_angle_degrees=np.rad2deg(pitch_angle_rad)
        print("Pitch angle rad:",pitch_angle_rad,'\n')
        #print("Pitch angle degrees:",pitch_angle_degrees,'\n')
        
        

        #Plane3
        p=x_position[int(len(x_position)/2)]
        q=y_position[int(len(y_position)/2)]
        #Threshold values
        t_x=200
        t_y=100
        altitude=300 #80 meters high = 80000 mm
        if p>t_x and q>t_y:
            m=np.array([p,q+50,altitude*focal_length_pixel/focal_length_mm])
            n=np.array([p+100,q+100,altitude*focal_length_pixel/focal_length_mm])
            l=np.array([p-100,img_height,(altitude-0.4)*focal_length_pixel/focal_length_mm])
        else:
            m=np.array([p+t_x,q+t_y+50,altitude*focal_length_pixel/focal_length_mm])
            n=np.array([p+t_x+100,q+t_y+100,altitude*focal_length_pixel/focal_length_mm])
            l=np.array([p+t_x-100,img_height,(altitude-0.4)*focal_length_pixel/focal_length_mm])

        center3,vec3=estimate_plane(m, n, l)
        #print(center3,vec3,'\n')
        rotation_matrix=rotation_matrix_from_vectors(vec3, vec1)
        print('Plane Rotation Matrix: ',rotation_matrix,'\n')
        
        #Plane Results
        rotated=np.dot(rotation_matrix,vec3)
        vec1_unit=(vec1 / np.linalg.norm(vec1)).reshape(3)
        vec3_unit_rotated=(rotated / np.linalg.norm(rotated)).reshape(3)
        print('Vec1_unit: ',vec1_unit,'\n')
        print('Vec3_rotated_unit: ',vec3_unit_rotated,'\n')
        theta_x=np.arctan2(rotation_matrix[2,1],rotation_matrix[2,2])
        print('Theta x rad: ',theta_x)
        theta_y=np.arctan2(-rotation_matrix[2,0],np.sqrt((rotation_matrix[2,1])**2+(rotation_matrix[2,2])**2))
        print('Theta y rad: ',theta_y)
        theta_z=np.arctan2(rotation_matrix[1,0],rotation_matrix[0,0])
        print('Theta z rad: ',theta_z,'\n')


        te=time.time()
        print('--- %s seconds ---'%(te-ts),'\n')
        print("---------------------")




        plt.subplot(211),plt.imshow(img,cmap = 'gray')
        plt.title('Image'), plt.xticks([]), plt.yticks([])  
 
        
        plt.subplot(212),plt.imshow(img,cmap = 'gray')
        plt.title('Motion Prediction'), plt.xticks([]), plt.yticks([]) 
        #plt.scatter(x_position, y_position,c='y',s=1)
        plt.scatter(x_line, y_line,s=0.1, c='r')
        plt.scatter(x_position_predict, y_position_predict,s=0.1, c='g')

        plt.show()

        #Compensate Movement
        plt.subplot(121),plt.imshow(img_reference,cmap = 'gray')
        plt.title('Reference Image'), plt.xticks([]), plt.yticks([])
        plt.subplot(122),plt.imshow(allign_image_pitch_roll,cmap = 'gray')
        plt.title('Compensated Image'), plt.xticks([]), plt.yticks([]) 
        plt.show()