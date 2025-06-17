#include "kernel/types.h"
#include "kernel/stat.h"
#include "user/user.h"

void primes(int fd) __attribute__((noreturn)); // Khai báo để tránh lỗi đệ quy vô hạn

void primes(int fd) {
    int num;

    if (read(fd, &num, sizeof(num)) == 0) {
        close(fd);
        exit(0);
    }

    printf("prime %d\n", num);

    int p[2];
    pipe(p);

    if (fork() == 0) {
        // Tiến trình con: tiếp tục xử lý với các số nguyên còn lại
        close(p[1]); // Đóng đầu ghi của pipe mới vì tiến trình con sẽ chỉ đọc
        close(fd);  // Đóng đầu đọc cũ vì không còn cần thiết nữa
        primes(p[0]); // Gọi đệ quy để xử lý tiếp
        close(p[0]); 
    } else {
        close(p[0]); // Đóng đầu đọc của pipe
        int tmp;
        while (1) {
            int n = read(fd, &tmp, sizeof(tmp));
            if (n <= 0) {
                break; // Không còn số để đọc từ pipe
            }
            if (tmp % num != 0) {
                write(p[1], &tmp, sizeof(tmp)); // Ghi số vào pipe nếu không chia hết cho `num`
            }
        }
        close(p[1]); // Đóng đầu ghi của pipe mới
        close(fd);  // Đóng pipe cũ
        wait(0); // Đợi tiến trình con kết thúc
   
        // Chương trình cha chỉ thoát sau khi tất cả tiến trình con đã kết thúc
        exit(0);
    }
}

int main(int argc, char *argv[]) {
    int p[2];
    pipe(p); // Tạo pipe

    // Tạo tiến trình con
    if (fork() == 0) { 
    // Tiến trình con
        close(p[1]);  // Đóng đầu ghi
        primes(p[0]); // Bắt đầu sàng lọc các số nguyên tố từ pipe
    } else {
        // Tiến trình cha
        close(p[0]);  // Đóng đầu đọc

        // Ghi các số từ 2 đến 280 vào pipe
        for (int i = 2; i <= 350; i++) { 
            write(p[1], &i, sizeof(i)); // Ghi số nguyên trực tiếp vào pipe
        }
        close(p[1]); // Đóng đầu ghi sau khi hoàn thành ghi các số
        wait(0);
        exit(0); // Kết thúc chương trình chính
    }
}
