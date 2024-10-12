#version 330


#if defined VERTEX_SHADER

// Model geometry
in vec3 in_position;
in vec3 in_normal;

// Per instance data
in vec3 in_offset;
in int  in_block_id;

uniform mat4 m_model;
uniform mat4 m_camera;
uniform mat4 m_proj;

out vec3 pos;
out vec3 normal;
flat out int block_id;

void main() {
    mat4 m_view = m_camera * m_model;

    vec3 position = in_position;
    position += in_offset;

    vec4 p = m_view * vec4(position, 1.0);
    gl_Position =  m_proj * p;
    
    mat3 m_normal = inverse(transpose(mat3(m_view)));
    normal = m_normal * normalize(in_normal);
    pos = p.xyz;

    block_id = in_block_id;
}

#elif defined FRAGMENT_SHADER

#define BLOCK_NONE 0
#define BLOCK_GRASS 1
#define BLOCK_DIRT 2
#define BLOCK_WATER 3

out vec4 fragColor;

flat in int  block_id;
in vec3 pos;
in vec3 normal;


void main() {
    vec4 color;
    if (block_id == BLOCK_DIRT) {
        color = vec4(0.5, 0.3, 0.0, 1.0);
    } else if (block_id == BLOCK_GRASS) {
        color = vec4(0.0, 0.5, 0.0, 1.0);
    } else if (block_id == BLOCK_WATER) {
        color = vec4(0.0, 0.0, 1.0, 1.0);
    } else if (block_id == BLOCK_NONE) {
        color = vec4(0.2, 0.2, 0.2, 0.0);
    } else {
        color = vec4(1.0, 1.0, 0.0, 1.0);
    } 

    float l = dot(normalize(-pos), normalize(normal));

    fragColor = color * (0.25 + abs(l) * 0.60);

}
#endif