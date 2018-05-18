//exponential convolutions


// scalar functions

__kernel void conv_x(__global float * input,
						__global float * output,
						  const int Nh){

  int i = get_global_id(0);
  int j = get_global_id(1);
  
  int Nx = get_global_size(0);

  float res = 0.f;
  float sum_val= 0.f;
  int start = i-Nh/2;

  const int h_start = ((i-Nh/2)<0)?Nh/2-i:0;
  const int h_end = ((i+Nh/2)>=Nx)?Nh-(i+Nh/2-Nx+1):Nh;

  for (int ht = h_start; ht< h_end; ++ht){
      float val = native_exp((float)(-10.f*(ht-Nh/2.f)*(ht-Nh/2.f)/Nh/Nh));
      sum_val += val;
      res += val*input[start+ht+j*Nx];
  }



	
  output[i+j*Nx] = res/sum_val;
}

__kernel void conv_y(__global float * input,
						__global float * output,
						  const int Nh){

  int i = get_global_id(0);
  int j = get_global_id(1);
  
  int Nx = get_global_size(0);
  int Ny = get_global_size(1);

  float res = 0.f;
  float sum_val= 0.f;

  int start = j-Nh/2;

  const int h_start = ((j-Nh/2)<0)?Nh/2-j:0;
  const int h_end = ((j+Nh/2)>=Ny)?Nh-(j+Nh/2-Ny+1):Nh;

  
  for (int ht = h_start; ht< h_end; ++ht){
       float val = native_exp((float)(-10.f*(ht-Nh/2.f)*(ht-Nh/2.f)/Nh/Nh));
      sum_val += val;
      res += val*input[i+(start+ht)*Nx];
  }

	
  output[i+j*Nx] = res/sum_val;
}

// 3d vector functions

__kernel void conv_vec_x(__global float * input,
						__global float * output,
						  const int Nh){

  int i = get_global_id(0);
  int j = get_global_id(1);

  int Nx = get_global_size(0);

  float res_x = 0.f;
  float res_y = 0.f;
  float res_z = 0.f;

  float sum_val= 0.f;

  int start = i-Nh/2;

  const int h_start = ((i-Nh/2)<0)?Nh/2-i:0;
  const int h_end = ((i+Nh/2)>=Nx)?Nh-(i+Nh/2-Nx+1):Nh;

  for (int ht = h_start; ht< h_end; ++ht){
      float val = native_exp((float)(-5.f*(ht-Nh/2.f)*(ht-Nh/2.f)/Nh/Nh));
      sum_val += val;
      res_x += val*input[0+3*(start+ht)+3*j*Nx];
      res_y += val*input[1+3*(start+ht)+3*j*Nx];
      res_z += val*input[2+3*(start+ht)+3*j*Nx];
  }




  output[0+3*(i+j*Nx)] = res_x/sum_val;
  output[1+3*(i+j*Nx)] = res_y/sum_val;
  output[2+3*(i+j*Nx)] = res_z/sum_val;
}

__kernel void conv_vec_y(__global float * input,
						__global float * output,
						  const int Nh){

  int i = get_global_id(0);
  int j = get_global_id(1);

  int Nx = get_global_size(0);
  int Ny = get_global_size(1);

  float res_x = 0.f;
  float res_y = 0.f;
  float res_z = 0.f;


  float sum_val= 0.f;

  int start = j-Nh/2;

  const int h_start = ((j-Nh/2)<0)?Nh/2-j:0;
  const int h_end = ((j+Nh/2)>=Ny)?Nh-(j+Nh/2-Ny+1):Nh;


  for (int ht = h_start; ht< h_end; ++ht){
       float val = exp((float)(-5.f*(ht-Nh/2.f)*(ht-Nh/2.f)/Nh/Nh));
      sum_val += val;
      res_x += val*input[0+3*(i+(start+ht)*Nx)];
      res_y += val*input[1+3*(i+(start+ht)*Nx)];
      res_z += val*input[2+3*(i+(start+ht)*Nx)];
  }


  output[0+3*(i+j*Nx)] = res_x/sum_val;
  output[1+3*(i+j*Nx)] = res_y/sum_val;
  output[2+3*(i+j*Nx)] = res_z/sum_val;

}





