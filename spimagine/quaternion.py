import numpy as np

class Quaternion():
    def __init__(self,w=1.,x=0.,y=0.,z=0.):
        self.data = np.array([w,x,y,z])

    @classmethod
    def copy(cls,rhs):
        return Quaternion(*rhs.data)

    def __getitem__(self,i):
        return self.data[i]

    def __setitem__(self,i,val):
        self.data[i] = val



    def conj(self):
        return Quaternion(self[0],-self[1],-self[2],-self[2])

    def norm(self):
        return np.linalg.norm(self.data)

    def __add__(self,q):
        return Quaternion(self.data+q.data)

    def __sub__(self,q):
        return Quaternion(self.data-q.data)


    def __mul__(self,q):
        if hasattr(q,"data"):
        # if isinstance(q,Quaternion):
            a1,b1,c1,d1 = self.data
            a2,b2,c2,d2 = q.data
            return Quaternion(a1*a2 - b1*b2 - c1*c2 - d1*d2,
                          a1*b2 + b1*a2 + c1*d2 - d1*c2,
                          a1*c2 - b1*d2 + c1*a2 + d1*b2,
                          a1*d2 + b1*c2 - c1*b2 + d1*a2)
        else:
            print "scalar multiplication!"
            return Quaternion(*(q*self.data))

    def __repr__(self):
        return str(self.data)


    def normalize(self):
        return Quaternion(*(self.data*1./self.norm()))

    def toRotation4(self):
        a,b,c,d = self.data
        return np.array([
    [a**2+b**2-c**2-d**2, 2*(b*c-a*d), 2*(b*d+a*c),0],
    [2*(b*c+a*d), a**2-b**2+c**2-d**2, 2*(c*d-a*b),0],
    [2*(b*d-a*c), 2*(c*d+a*b),  a**2-b**2-c**2+d**2,0],
    [0,0,0,1]
    ])

    def toRotation3(self):
        a,b,c,d = self.data
        return np.array([
    [a**2+b**2-c**2-d**2, 2*(b*c-a*d), 2*(b*d+a*c)],
    [2*(b*c+a*d), a**2-b**2+c**2-d**2, 2*(c*d-a*b)],
    [2*(b*d-a*c), 2*(c*d+a*b),  a**2-b**2-c**2+d**2],
    ])



if __name__ == '__main__':
    q = Quaternion(2,0,0,0)

    q = q.normalize()

    q2 = q

    print q
    print q2


    q2[0] = 99.

    print q
    print q2
