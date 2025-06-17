#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"
#include "kernel/fs.h"


char* fmtname(char *path)
{
  static char buf[DIRSIZ+1];
  char *p;

  // Find first character after last slash.
  for(p=path+strlen(path); p >= path && *p != '/'; p--);
  p++;

  if(strlen(p) >= DIRSIZ)
    return p;
  memmove(buf, p, strlen(p));
  memset(buf+strlen(p), '\0', DIRSIZ-strlen(p));
  return buf;
}

void find(char *path, char *search_exp, int *flag)
{
  char buf[512];
  char *p;
  int fd;
  // struct dirent là một cấu trúc dữ liệu đại diện cho một mục trong thư mục. Nó chứa thông tin cơ bản 
  // về một file hoặc thư mục trong một thư mục cha.
  struct dirent de;
  struct stat st;
  // struct stat là một cấu trúc dữ liệu chứa thông tin chi tiết về một file hoặc thư mục

  //Check some errors of path
  // +1: là ký tự '/'
  // + DIRSIZ: kích thước tối đa của file hoặc thư mục
  // + 1: \0 là ký tự kết thúc chuỗi  
  if(strlen(path) + 1 + DIRSIZ + 1 > 512){   // 512, là giới hạn kích thước buffer được định nghĩa trong chương trình.
    fprintf(2, "find: path too long\n");
    return;
  }

    //0: open path with read only mode
  if((fd = open(path, 0)) < 0){
    fprintf(2, "find: path %s doesn't not exist\n", path);
    return;
  }

    //fstat function can't retrieve infor of path
  if(fstat(fd, &st) < 0){ // hàm lấy meta data của thư mục
    fprintf(2, "find: unknown path %s\n", path);
    close(fd);
    return;
  }

  strcpy(buf, path);
  p = buf + strlen(buf);
  *p++ = '/';

  while(read(fd, &de, sizeof(de)) == sizeof(de)){
    // Trường inum trong struct dirent là số inode tương ứng với mục này trong thư mục.
    if(de.inum == 0)  // mục hiện tại không hợp lệ hoặc không sử dụng (một mục "trống").
      continue;

    // de.name chứa tên của mục (file hoặc thư mục) hiện tại trong thư mục.
    memmove(p, de.name, DIRSIZ);      // Sử dụng DIRSIZ để giới hạn độ dài tên được sao chép
    p[DIRSIZ] = 0;    // Ký tự kết thúc

    if(stat(buf, &st) < 0){
      printf("find: cannot stat %s\n", buf); 
      continue;
    }

    // nếu là file
    if (st.type == T_FILE){
      if (strcmp(fmtname(buf), search_exp) == 0) {
        *flag = 1; // Mark file found
        printf("%s\n", buf);
      }
    } else if (st.type == T_DIR){   // nếu là thư mục
      // Don't recurse into "." and "..".
      if (strcmp(fmtname(buf), ".") != 0 && strcmp(fmtname(buf), "..") != 0) {
        // Get new metadata for directory file
        int fd2 = open(buf, 0);
        // Recursive search in found directory
        find(buf, search_exp, flag);
        close(fd2);
      }
    }
  }
  close(fd);
}

int main(int argc, char *argv[])
{
  int flag = 0;

  if(argc < 3 || argc > 4)
  {
    printf("Usage: find [path] [expression]\n");
    exit(1);
  } 
  else
  {
    find(argv[1], argv[2], &flag);
  }

  // Notification if file not found
  if (!flag)
  {
    printf("find: file not found\n");
  }

  return 0;
}
