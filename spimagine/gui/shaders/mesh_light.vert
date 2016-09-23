//attribute vec3 position;
//attribute vec3 normal;
//
//uniform mat4 mvpMatrix;
//uniform mat4 normMatrix;
//
//varying vec4 var_normal;
//varying vec4 var_pos;
//
//
//
//void main()
//{
//
//  vec3 pos = position;
//  var_pos = mvpMatrix *vec4(pos, 1.0);
//
//  gl_Position = var_pos;
//  var_normal = normalize(normMatrix *vec4(normal, 0.0));
//}

attribute vec3 position;
attribute vec3 normal;



uniform mat4 normMatrix;
uniform mat4 mvpMatrix;
uniform mat4 mvMatrix;


varying vec3 var_normal;
varying vec3 var_pos;

void main()
{

  var_normal = normalize((normMatrix*vec4(normal,1.)).xyz);
  var_pos = (mvMatrix *vec4(position, 1.0)).xyz;

  gl_Position  = mvpMatrix *vec4(position, 1.0);


}
