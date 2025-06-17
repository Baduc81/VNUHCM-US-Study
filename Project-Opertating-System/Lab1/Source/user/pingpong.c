#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

int main() {
  int p[2]; // pipe từ cha sang con
  int q[2]; // pipe từ con sang cha
  char buf[100];
  char byte;

  // Tạo 2 pipe
  pipe(p);
  pipe(q);

  // Tạo tiến trình con
  int pid = fork();

  if (pid < 0) {
    // Nếu fork thất bại
    printf("Fork failed!\n");
    exit(1);
  }
  else if (pid == 0) {
    // Tiến trình con: gửi tin nhắn cho tiến trình cha
    // Đọc từ ống dẫn p (cha sang con)
    read(p[0], &buf, 1);
    // In ra thông báo
    printf("%d: received ping\n", getpid());
    // Ghi byte lên ống dẫn q (con sang cha)
    write(q[1], &buf, 1);
    // Kết thúc tiến trình con
    exit(0);
  } 
  else {
    // Tiến trình cha: đợi tiến trình con, sau đó đọc tin nhắn
    write(p[1], &byte, 1);
    // Đợi tiến trình con kết thúc và đọc từ ống dẫn q (con sang cha)
    read(q[0], &buf, 1);
    // In ra thông báo
    printf("%d: received pong\n", getpid());
    // Kết thúc tiến trình cha
    exit(0);
  }
}
