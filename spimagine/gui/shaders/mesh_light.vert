attribute vec3 position;
attribute vec3 normal;

uniform mat4 mvpMatrix;
uniform mat4 mvpNormalMatrix;

varying vec4 var_normal;
varying vec4 var_pos;



void main()
{
  //vec3 pos = position;
  //var_pos = mvpMatrix *vec4(pos, 1.0);
  gl_Position = var_pos;


  //var_normal = mvpNormalMatrix *vec4(normal, 0.0);;
}
