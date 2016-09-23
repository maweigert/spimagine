//uniform vec4 color;
////uniform vec3 light;
//
//varying vec4 var_pos;
//varying vec4 var_normal;
//
//void main()
//{
//
//
//  //vec3 refl = reflect(-light, var_normal);
//  //vec3 view = normalize(-vec3(var_pos)/var_pos.w);
//  //float lamb = max(dot(light,-var_normal), 0.0);
//
//
//  //gl_FragColor = color*lamb;
//
//
//  gl_FragColor = color;
//
//}
//


uniform vec4 color;
uniform vec3 light;
uniform vec3 light_components;

varying vec3 var_normal;
varying vec3 var_pos;



void main()
{


    //Phong shading

   vec3 L = normalize(light - var_pos);
   vec3 E = normalize(-var_pos);
   vec3 R = normalize(-reflect(L,var_normal));

   //calculate Diffuse Term:
   float c_diffuse = max(dot(var_normal,L), 0.0);
   c_diffuse = clamp(c_diffuse, 0.0, 1.0);

   // calculate Specular Term:
   float c_spec= pow(max(dot(R,E),0.0),10.);
   c_spec = clamp(c_spec, 0.0, 1.0);

   float mag = (light_components.x+light_components.y*c_diffuse+light_components.z*c_spec);


   gl_FragColor = mag*color;


}
