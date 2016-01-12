attribute vec3 position;


uniform mat4 mvpMatrix;




void main()
{
  vec3 pos = position;
  gl_Position = mvpMatrix *vec4(pos, 1.0);

}
