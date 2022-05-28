#ifndef LZSS_H
#define LZSS_H

typedef unsigned char byte;
int lzss_compress(int EI, int EJ, int P, int rless, uint8_t* buffer, const uint8_t* src, int srclen, uint8_t* dst);
void lzss_decompress(
    int EI, int EJ, int P, int rless, byte* buffer, 
    const byte* srcstart, int srclen, byte* dststart, int dstlen
);

#endif

