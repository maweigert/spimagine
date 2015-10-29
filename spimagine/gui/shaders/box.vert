attribute vec3 position;
uniform mat4 mvpMatrix;

varying float zPos;
varying vec2 texcoord;
void main()
{
  vec3 pos = position;
  gl_Position = mvpMatrix *vec4(pos, 1.0);

  texcoord = .5*(1.+.98*gl_Position.xy/gl_Position.w);
  zPos = 0.04+gl_Position.z;
}
