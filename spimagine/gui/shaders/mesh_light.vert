attribute vec3 position;
attribute vec3 normal;

uniform mat4 mvpMatrix;
uniform mat4 mvpNormalMatrix;

varying vec4 var_normal;
varying vec4 var_pos;



void main()
{

  vec3 pos = position;
  gl_Position = mvpMatrix *vec4(pos, 1.0);

  var_pos = mvpMatrix *vec4(pos, 1.0);
  var_normal = normalize(mvpNormalMatrix *vec4(normal, 0.0));
}
