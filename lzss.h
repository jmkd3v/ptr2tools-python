#ifndef LZSS_H
#define LZSS_H

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

typedef unsigned char byte;
EXPORT int lzss_compress(int EI, int EJ, int P, int rless, uint8_t* buffer, const uint8_t* src, int srclen, uint8_t* dst);
EXPORT void lzss_decompress(
    int EI, int EJ, int P, int rless, byte* buffer, 
    const byte* srcstart, int srclen, byte* dststart, int dstlen
);

#endif

