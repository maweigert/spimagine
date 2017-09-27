uniform sampler2D texture;
uniform sampler2D texture_LUT;
uniform bool is_mode_black;
varying vec2 mytexcoord;

void main()
{
   vec4 col = texture2D(texture,mytexcoord);

   vec4 lut;

   if (is_mode_black)
     lut = texture2D(texture_LUT,col.xy);
   else
     lut = texture2D(texture_LUT,vec2(1.,1.)-col.xy);

   //vec4 lut = texture2D(texture_LUT,col.xy);

  gl_FragColor = vec4(lut.xyz,1.);

  gl_FragColor.w = 1.0*length(gl_FragColor.xyz);
  gl_FragColor.w = 1.0;


}