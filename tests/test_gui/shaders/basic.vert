attribute vec2 position;
attribute vec3 color;
varying vec3 var_color;


void main()
{
    gl_Position = vec4(position,0,1.);

    var_color = color;

}
