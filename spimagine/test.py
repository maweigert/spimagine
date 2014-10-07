from numpy import *



def slice_coords(relPos,dim):

    if dim ==0:
        coords = array([[0,-1,-1],[0,1,-1],[0,1,1],
                    [0,1,1],[0,-1,1],[0,-1,-1]],dtype=float32)

    elif dim ==1:
        coords = array([[-1,0,-1],[1,0,-1],[1,0,1],
                    [1,0,1],[-1,0,1],[-1,0,-1]],dtype=float32)

    elif dim ==2:
        coords = array([[-1,-1,0],[1,-1,0],[1,1,0],
                    [1,1,0],[-1,1,0],[-1,-1,0]],dtype=float32)


    coords[:,dim] = -1.+2*relPos

    print coords[:,dim]
    return coords

if __name__ == '__main__':


    coords = slice_coords(.1,0)

    print coords
