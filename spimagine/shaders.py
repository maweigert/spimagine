vertShaderTex ="""
attribute vec2 position;
attribute vec2 texcoord;
varying vec2 mytexcoord;

void main()
{
    gl_Position = vec4(position, 0., 1.0);
    mytexcoord = texcoord;
}
"""

fragShaderTex = """
uniform sampler2D texture;
uniform sampler2D texture_LUT;
varying vec2 mytexcoord;

void main()
{
  vec4 col = texture2D(texture,mytexcoord);

  vec4 lut = texture2D(texture_LUT,col.xy);

  gl_FragColor = vec4(lut.xyz,col.x);
//  gl_FragColor.w = 1.0*length(gl_FragColor.xyz);

}
"""

vertShaderCube ="""
attribute vec3 position;
uniform mat4 mvpMatrix;

void main()
{
  vec3 pos = position;
  gl_Position = mvpMatrix *vec4(pos, 1.0);

}
"""

fragShaderCube = """
void main()
{
  gl_FragColor = vec4(1.,1.,1.,.6);
}
"""
