attribute vec3 position;
uniform mat4 mvpMatrix;
attribute vec2 texcoord;
varying vec2 mytexcoord;

void main()
{
    vec3 pos = position;
    gl_Position = mvpMatrix *vec4(pos, 1.0);

    mytexcoord = texcoord;
}
