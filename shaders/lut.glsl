#version 330
#define SHADER_TYPE
#define DIFFUSION_PROFILE
#ifdef VERTEX_SHADER
in vec3 vertPos;
out float curvature;
out float cosTheta;
uniform float maxCurvature = 1.0;
void main()
{
    gl_Position = vec4(vertPos, 1.);
    curvature = clamp(0.5 * vertPos.y + 0.5, 0., 1.) * maxCurvature;
    cosTheta = vertPos.x;
}
#endif
#ifdef FRAGMENT_SHADER
const float PI = 3.1415926f;
const int NUM_SAMPLES = 1024;
uniform vec3 zr;
uniform vec3 zv;
uniform vec3 sigmaTr;
uniform vec3 albedo = vec3(1.0f);
in float curvature;
in float cosTheta;
out vec3 fragColor;
#ifdef GAUSSIAN
float Gaussian(float v, float r)
{
    return exp(-r * r / (2.0f * v)) / sqrt(2.0f * PI * v);
}
vec3 DiffusionProfile(float r)
{
    return vec3(0.233f, 0.455f, 0.649f) * Gaussian(0.000064f * 1.414f, r) +
        vec3(0.1f, 0.336f, 0.344f) * Gaussian(0.000484f * 1.414f, r) +
        vec3(0.118f, 0.198f, 0.0f) * Gaussian(0.00187f * 1.414f, r) +
        vec3(0.113f, 0.007f, 0.007f) * Gaussian(0.00567f * 1.414f, r) +
        vec3(0.358f, 0.004f, 0.0f) * Gaussian(0.0199f * 1.414f, r) +
        vec3(0.078f, 0.0f, 0.0f) * Gaussian(0.0741f * 1.414f, r);
}
#else
vec3 DiffusionProfile(float r)
{
    vec3 dr = sqrt(r * r + zr * zr);
    vec3 dv = sqrt(r * r + zv * zv);
    vec3 weight =
        1.0 / (4.0 * PI) * (
            zr * (sigmaTr * dr + 1.0) * exp(-sigmaTr * dr) / (dr * dr * dr) +
            zv * (sigmaTr * dv + 1.0) * exp(-sigmaTr * dv) / (dv * dv * dv)
        );
    return any(isnan(weight)) ? vec3(0.0) : weight;
}
#endif
void main()
{
    vec3 acc1 = vec3(0.), acc2 = vec3(0.);
    float theta = acos(cosTheta);
    float radius = 1. / curvature;
    for(int i = 0; i < NUM_SAMPLES; i++)
    {
        float x = PI * ((i + .5f) / NUM_SAMPLES - .5f);
        float dis = 2.0f * radius * sin(x * .5f);
        vec3 weight = DiffusionProfile(dis);
        acc1 += weight * clamp(cos(theta + x), 0.0f, 1.0f);
        acc2 += weight;
    }
    fragColor = pow(acc1 / acc2 * albedo, vec3(1.0 / 2.2));
}
#endif
