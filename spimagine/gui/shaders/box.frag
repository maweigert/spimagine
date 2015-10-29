
uniform vec4 color;
uniform sampler2D texture_alpha;
varying float zPos;
varying vec2 texcoord;
void main()
{

  // float tnear = texture2D(texture_alpha,mytexcoord.xy).x;

  float tnear = texture2D(texture_alpha,texcoord).x;

  float att = exp(-.5*(zPos-tnear));

  gl_FragColor = color*att;
}
