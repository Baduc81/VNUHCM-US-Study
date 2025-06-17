#include "kernel/types.h"
#include "user/user.h"
#include "kernel/fcntl.h"
#include "kernel/param.h"

#define BUFFER_SIZE 512

int main(int argc, char *argv[]) {
    char buffer[BUFFER_SIZE];
    char *cmd_argv[MAXARG];  // Mảng đối số cho lệnh
    int n; //, pid;
    // int i, j;

    if (argc < 2){
        fprintf(2, "Not have enough input");
        exit(1);
    }
    for (int i = 0; i < argc - 1; i++){
        cmd_argv[i] = argv[i + 1];
    } 

    cmd_argv[argc - 1] = 0;    // Ký tự kết thúc

    while ((n = read(0, buffer, sizeof(buffer))) > 0){
        int i = 0;
        while (i < n){
            char line[BUFFER_SIZE];
            int j = 0;
            while (i < n && buffer[i] != '\n'){
                line[j++] = buffer[i++];
            }

            if (buffer[i] == '\n'){
                i++;
            }

            line[j] = '\0';
            cmd_argv[argc - 1] = line;
            cmd_argv[argc] = 0;
            // cmd_argv = echo line line1
            int pid = fork();
            if (pid == 0) {
                exec(cmd_argv[0], cmd_argv);
                fprintf(2, "exec %s failed\n", cmd_argv[0]);
                exit(1);
            } else if (pid < 0) {
                fprintf(2, "fork failed\n");
                exit(1);
            } else {
                // Tiến trình cha đợi tiến trình con hoàn thành
                wait(0);
            }
        }  
    }
    exit(0);
}

// #include "kernel/types.h"
// #include "kernel/stat.h"
// #include "user/user.h"
// #include "kernel/param.h"  // MAXARG

// #define is_blank(chr) (chr == ' ' || chr == '\t') 

// int
// main(int argc, char *argv[])
// {
// 	char buf[2048], ch;
// 	char *p = buf;
// 	char *v[MAXARG];
// 	int c;
// 	int blanks = 0;
// 	int offset = 0;

// 	if(argc <= 1){
// 		fprintf(2, "usage: xargs <command> [argv...]\n");
// 		exit(1);
// 	}

// 	for (c = 1; c < argc; c++) {
// 		v[c-1] = argv[c];
// 	}
// 	--c;

// 	while (read(0, &ch, 1) > 0) {
// 		if (is_blank(ch)) {
// 			blanks++;
// 			continue;
// 		}

// 		if (blanks) {  // 之前有过空格
// 			buf[offset++] = 0;

// 			v[c++] = p;
// 			p = buf + offset;

// 			blanks = 0;
// 		}

// 		if (ch != '\n') {
// 			buf[offset++] = ch;
// 		} else {
// 			v[c++] = p;
// 			p = buf + offset;

// 			if (!fork()) {
// 				exit(exec(v[0], v));
// 			}
// 			wait(0);
			
// 			c = argc - 1;
// 		}
// 	}

// 	exit(0);
// }