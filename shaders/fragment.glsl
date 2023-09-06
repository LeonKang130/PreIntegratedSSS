#version 450
#define WITH_SPECULAR
in vec3 fragment_pos;
in vec3 fragment_normal;
out vec3 fragment_color;
uniform sampler2D lut;
uniform float min_curvature = 0.0f;
uniform float max_curvature = 1.0f;
const vec3 camera_pos = vec3(0.0, 1.0, 8.0);
struct PointLight
{
    vec3 emission;
    vec3 position;
};
struct DirectionLight
{
    vec3 emission;
    vec3 direction;
};
layout (std140, binding=0) uniform PointLightBuffer
{
    PointLight point_lights[32];
};
layout (std140, binding=1) uniform DirectionLightBuffer
{
    DirectionLight direction_lights[32];
};
uniform int num_point_lights = 0;
uniform int num_direction_lights = 0;
vec3 linearToSRGB(vec3 color)
{
    vec3 a = 1.055 * pow(color, vec3(1.0 / 2.4)) - 0.055;
    vec3 b = 12.92 * color;
    vec3 cut_off = vec3(lessThan(color, vec3(0.00031308)));
    return clamp(mix(a, b, cut_off), 0.0, 1.0);
}
void main()
{
    vec3 normal = normalize(fragment_normal);
    float curvature = length(fwidth(normal)) / length(fwidth(fragment_pos));
    curvature = clamp(curvature, min_curvature, max_curvature) / max_curvature;
    vec3 color = vec3(0.0f);
    vec3 view_dir = normalize(camera_pos - fragment_pos);
    for(int i = 0; i < num_point_lights; i++)
    {
        PointLight light = point_lights[i];
        vec3 light_dir = normalize(light.position - fragment_pos);
        float NDotL = dot(normal, light_dir);
        vec3 diffuse = pow(texture(lut, vec2(0.5 * NDotL + 0.5, curvature)).xyz, vec3(2.2f)) * light.emission;
        color += diffuse;
    }
    for(int i = 0; i < num_direction_lights; i++)
    {
        DirectionLight light = direction_lights[i];
        vec3 light_dir = normalize(light.direction);
        float NDotL = dot(normal, light_dir);
        vec3 diffuse = pow(texture(lut, vec2(0.5 * NDotL + 0.5, curvature)).xyz, vec3(2.2f)) * light.emission;
        color += diffuse;
    }
    fragment_color = linearToSRGB(color);
}
