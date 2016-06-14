uniform sampler2D texture;
uniform sampler2D texture_alpha;
uniform sampler2D texture_LUT;
uniform bool is_mode_black;
varying vec2 mytexcoord;


void main()
{
  vec4 col = texture2D(texture,mytexcoord);
  vec4 alph = texture2D(texture_alpha,mytexcoord);
  float tnear  = alph.x;

  vec4 lut;

  if (is_mode_black)
    lut = texture2D(texture_LUT,col.xy);
  else
    lut = texture2D(texture_LUT,vec2(1.,1.)-col.xy);

  gl_FragColor = vec4(lut.xyz,col.x);

  gl_FragColor.w = 1.0*length(col.xyz);

  if (tnear<0.0)
    gl_FragColor = vec4(0.,0.,0.,0.);


  //gl_FragColor = vec4(lut.x,.0,.0, 1.);
}
