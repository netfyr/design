/* Actual HarfBuzz shaping for every ordered encoded pair. No headers from
 * external font projects and no substitute glyphs are used. ABI definitions
 * match the public HarfBuzz C API. Profiles are generated from this font. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <time.h>
typedef struct {uint32_t codepoint,mask,cluster,v1,v2;} Info;
typedef struct {int32_t xa,ya,xo,yo;uint32_t var;} Pos;
extern void *hb_blob_create(const char*,unsigned,int,void*,void*);
extern void *hb_face_create(void*,unsigned),*hb_font_create(void*),*hb_buffer_create(void);
extern void hb_ot_font_set_funcs(void*),hb_font_set_scale(void*,int,int),hb_buffer_reset(void*);
extern void hb_buffer_add_utf32(void*,const uint32_t*,int,unsigned,int);
extern void hb_buffer_guess_segment_properties(void*),hb_shape(void*,void*,void*,unsigned);
extern Info *hb_buffer_get_glyph_infos(void*,unsigned*);
extern Pos *hb_buffer_get_glyph_positions(void*,unsigned*);
extern void hb_buffer_destroy(void*),hb_font_destroy(void*),hb_face_destroy(void*),hb_blob_destroy(void*);
extern const char *hb_version_string(void);
typedef struct {uint16_t count,flags;int16_t gap,optical,kern,overlap_rows;int32_t advance;} Result;
/* flags: 1 missing; 2 ink overlap candidate; 4 close (<18 units); 8 mark run;
 * 16 whitespace/control; 32 technical join; 64 contextual/complex shaping.
 * 128 positioned bounding boxes overlap: include in vector verification.
 * An overlap candidate is not automatically an invalid pair. */
static void *readall(const char *p,long *n){FILE*f=fopen(p,"rb");if(!f){perror(p);exit(1);}fseek(f,0,SEEK_END);*n=ftell(f);rewind(f);void*b=malloc(*n);if(fread(b,1,*n,f)!=(size_t)*n)exit(2);fclose(f);return b;}
int main(int argc,char**argv){
 if(argc!=4){fprintf(stderr,"font profiles.bin output.bin\n");return 1;}
 long fn,pn;char*fd=readall(argv[1],&fn);char*pd=readall(argv[2],&pn);int32_t*h=(int32_t*)pd;
 int ng=h[0],nc=h[1],rows=h[2],ytop=h[3],step=h[5];char*p=pd+24;
 uint32_t*cps=(uint32_t*)p;p+=4*nc;uint16_t*cf=(uint16_t*)p;p+=2*nc;uint16_t*cg=(uint16_t*)p;p+=2*nc;
 int16_t*adv=(int16_t*)p;p+=2*ng;int16_t*bb=(int16_t*)p;p+=8*ng;
 int16_t*left=(int16_t*)p;p+=2*ng*rows;int16_t*right=(int16_t*)p;
 void*blob=hb_blob_create(fd,fn,0,NULL,NULL),*face=hb_face_create(blob,0),*font=hb_font_create(face),*buf=hb_buffer_create();
 hb_ot_font_set_funcs(font);hb_font_set_scale(font,1000,1000);
 FILE*out=fopen(argv[3],"wb");if(!out){perror(argv[3]);return 2;}fwrite(h,4,6,out);
 uint64_t totals[8]={0},pairs=0;clock_t start=clock();Result*row=malloc(nc*sizeof(Result));
 for(int i=0;i<nc;i++){
  for(int j=0;j<nc;j++){
   uint32_t text[2]={cps[i],cps[j]};hb_buffer_reset(buf);hb_buffer_add_utf32(buf,text,2,0,2);hb_buffer_guess_segment_properties(buf);hb_shape(font,buf,NULL,0);
   unsigned n=0;Info*ii=hb_buffer_get_glyph_infos(buf,&n);Pos*pp=hb_buffer_get_glyph_positions(buf,&n);
   Result z={0};z.count=n;z.gap=30000;z.optical=30000;int px[20],py[20],x=0,y=0;
   if(n>20){fprintf(stderr,"excess shaping output\n");return 3;}
   for(unsigned k=0;k<n;k++){if(ii[k].codepoint==0)z.flags|=1;px[k]=x+pp[k].xo;py[k]=y+pp[k].yo;x+=pp[k].xa;y+=pp[k].ya;}
   z.advance=x;z.kern=x-adv[cg[i]]-adv[cg[j]];
   if((cf[i]|cf[j])&1)z.flags|=8;
   if((cf[i]|cf[j])&2)z.flags|=16;
   if((cf[i]&4)&&(cf[j]&4))z.flags|=32;
   if(n!=2||(n>1&&(ii[0].cluster!=0||ii[1].cluster!=1||pp[0].yo||pp[1].yo)))z.flags|=64;
   /* Every glyph in a run is checked against each later glyph. */
   int mingap=30000,over=0;int64_t sum=0;int samples=0;
   for(unsigned a=0;a<n;a++)for(unsigned b=a+1;b<n;b++){
    int ga=ii[a].codepoint,gb=ii[b].codepoint;if(ga>=ng||gb>=ng){z.flags|=1;continue;}
    if(bb[ga*4+3]==bb[ga*4+1]||bb[gb*4+3]==bb[gb*4+1])continue;
    int ya=py[a],yb=py[b];int bot=bb[ga*4+1]+ya,top=bb[ga*4+3]+ya;
    if(bb[gb*4+1]+yb>bot)bot=bb[gb*4+1]+yb;
    if(bb[gb*4+3]+yb<top)top=bb[gb*4+3]+yb;
    if(top>bot && bb[ga*4+2]+px[a]>bb[gb*4]+px[b]
               && bb[gb*4+2]+px[b]>bb[ga*4]+px[a]) z.flags|=128;
    for(int yy=bot+1;yy<top;yy+=step){
     int ra=(ytop-(yy-ya))/step,rb=(ytop-(yy-yb))/step;if(ra<0||ra>=rows||rb<0||rb>=rows)continue;
     int ar=right[ga*rows+ra],bl=left[gb*rows+rb];if(ar==-30000||bl==30000)continue;
     int gap=px[b]+bl-px[a]-ar;if(gap<mingap)mingap=gap;if(gap<0)over++;
     if(yy>=0&&yy<=700){sum+=gap<400?gap:400;samples++;}
    }
   }
   z.gap=mingap;z.overlap_rows=over>32767?32767:over;if(samples)z.optical=sum/samples;
   if(mingap<0)z.flags|=2;else if(mingap<18)z.flags|=4;
   for(int bit=0;bit<8;bit++)if(z.flags&(1<<bit))totals[bit]++;
   row[j]=z;pairs++;
  }
  if(fwrite(row,sizeof(Result),nc,out)!=(size_t)nc)return 4;
  if((i+1)%250==0){printf("%d/%d first characters; %llu ordered pairs\n",i+1,nc,(unsigned long long)pairs);fflush(stdout);}
 }
 fclose(out);printf("{\"harfbuzz\":\"%s\",\"characters\":%d,\"ordered_pairs\":%llu,\"missing\":%llu,\"overlap_candidates\":%llu,\"close_candidates\":%llu,\"mark_pairs\":%llu,\"space_control_pairs\":%llu,\"technical_pairs\":%llu,\"contextual_pairs\":%llu,\"bounding_box_candidates\":%llu,\"cpu_seconds\":%.3f,\"record_bytes\":%zu}\n",hb_version_string(),nc,(unsigned long long)pairs,(unsigned long long)totals[0],(unsigned long long)totals[1],(unsigned long long)totals[2],(unsigned long long)totals[3],(unsigned long long)totals[4],(unsigned long long)totals[5],(unsigned long long)totals[6],(unsigned long long)totals[7],(double)(clock()-start)/CLOCKS_PER_SEC,sizeof(Result));
 hb_buffer_destroy(buf);hb_font_destroy(font);hb_face_destroy(face);hb_blob_destroy(blob);free(row);free(fd);free(pd);return 0;
}
