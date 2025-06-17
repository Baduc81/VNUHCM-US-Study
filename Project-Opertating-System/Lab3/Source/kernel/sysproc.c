#include "types.h"
#include "riscv.h"
#include "param.h"
#include "defs.h"
#include "memlayout.h"
#include "spinlock.h"
#include "proc.h"

uint64
sys_exit(void)
{
  int n;
  argint(0, &n);
  exit(n);
  return 0;  // not reached
}

uint64
sys_getpid(void)
{
  return myproc()->pid;
}

uint64
sys_fork(void)
{
  return fork();
}

uint64
sys_wait(void)
{
  uint64 p;
  argaddr(0, &p);
  return wait(p);
}

uint64
sys_sbrk(void)
{
  uint64 addr;
  int n;

  argint(0, &n);
  addr = myproc()->sz;
  if(growproc(n) < 0)
    return -1;
  return addr;
}

uint64
sys_sleep(void)
{
  int n;
  uint ticks0;


  argint(0, &n);
  acquire(&tickslock);
  ticks0 = ticks;
  while(ticks - ticks0 < n){
    if(killed(myproc())){
      release(&tickslock);
      return -1;
    }
    sleep(&ticks, &tickslock);
  }
  release(&tickslock);
  return 0;
}

#ifdef LAB_PGTBL
uint64
sys_pgaccess(void)
{
  int num_pages;
  uint64 start_va;
  uint64 buffer_addr;

  argaddr(0, &start_va);
  argint(1, &num_pages);
  argaddr(2, &buffer_addr);

  // Validate the number of pages
  if (num_pages <= 0 || num_pages > 32) {
    return -1; // Limit to 32 pages (adjust as needed)
  }

  uint64 buf = 0; // Initialize buffer to 0
  struct proc *p = myproc(); // Get current process

  for (int i = 0; i < num_pages; i++) {
    uint64 va = (uint64)(start_va + i * PGSIZE); // Cast to uint64
    pte_t *pte = walk(p->pagetable, va, 0);   // Hàm này lấy con trỏ đến PTE của một địa chỉ ảo cụ thể trong bảng trang.

    if (!pte || !(*pte & PTE_V)) {
      continue; // Invalid page, skip
    }

    if (*pte & PTE_A) {
        buf |= (1ULL << i); // Set bit thứ i trong buf nếu trang đã được truy cập.
        *pte &= ~PTE_A; // Clear the access bit
    }
  }
  /*
  1ULL là cách viết trong C/C++ để biểu diễn một số nguyên không dấu (unsigned integer) có kích thước 64-bit (unsigned long long). Cụ thể:

  1: Đây là giá trị số nguyên (integer) ban đầu.
  U: Ký hiệu cho unsigned (số nguyên không dấu).
  LL: Ký hiệu cho long long, đảm bảo số nguyên có kích thước ít nhất 64-bit.
  */
  if (copyout(p->pagetable, buffer_addr, (char *)&buf, sizeof(buf)) < 0) { // Cast buffer_addr to uint64
      return -1;
  }

  return 0;
}
#endif

uint64
sys_kill(void)
{
  int pid;

  argint(0, &pid);
  return kill(pid);
}

// return how many clock tick interrupts have occurred
// since start.
uint64
sys_uptime(void)
{
  uint xticks;

  acquire(&tickslock);
  xticks = ticks;
  release(&tickslock);
  return xticks;
}


