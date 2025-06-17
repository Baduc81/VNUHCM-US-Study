#include "types.h"
#include "riscv.h"
#include "defs.h"
#include "param.h"
#include "memlayout.h"
#include "spinlock.h"
#include "proc.h"
#include "sysinfo.h"

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
  if(n < 0)
    n = 0;
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

uint64
sys_trace(void)
{
  int trace_mask;
  argint(0,&trace_mask);

  // argint failed
  if(trace_mask < 0){
    return -1; 
  }

  struct proc*p=myproc();
  p->traced = trace_mask;
	return 0;

}

uint64
sys_sysinfo(void)
{
  struct proc *p = myproc();  // Get current progress information.
  struct sysinfo info;        // Create a struct to save information.

  uint64 info_addr;           // user pointer to struct stat
  // Là địa chỉ (pointer) trong vùng user space, nơi cấu trúc sysinfo sẽ được sao chép sau khi hoàn thành việc tính toán.
  
  argaddr(0, &info_addr); // Hàm này lấy đối số đầu tiên của lệnh gọi hệ thống (syscall) từ vùng user space.
  // info_addr sẽ chứa địa chỉ của cấu trúc sysinfo trong không gian người dùng (user space), nơi thông tin sẽ được sao chép.
  
  info.freemem = free_memory();
  info.nproc = getnproc();
  info.loadavg = get_loadavg();

  // Copy the info back to the user space structure.
  if (copyout( p->pagetable, info_addr, (char*)&info, sizeof(info)) < 0){ // Hàm này được sử dụng để sao chép dữ liệu từ kernel space (vùng nhân) sang user space (vùng người dùng).
    return -1;
  }

  /*
  p->pagetable: Bảng trang của tiến trình hiện tại, dùng để ánh xạ địa chỉ kernel sang địa chỉ user space.
  info_addr: Địa chỉ trong user space, nơi thông tin cần được sao chép đến.
  (char*)&info: Con trỏ đến dữ liệu trong kernel space (ở đây là cấu trúc info).
  sizeof(info): Kích thước dữ liệu cần sao chép.
  */
  return 0;
}