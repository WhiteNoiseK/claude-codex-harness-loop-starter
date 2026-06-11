# Firmware Coding Protocol

> **[Optional — excluded by default (opt-in)]** This protocol is **excluded from the default harness scope**.
> Adopt it explicitly only in projects that write MCU firmware directly. Pure SW/web projects ignore it.
> (The core value of harness engineering is automated SW coding; firmware/RTL is kept as a safety boundary by default.)
>
> Target example: a multi-channel sensor/control board based on {{MCU_FAMILY}} (e.g. STM32L4 / nRF52).
> For naming/language rules see [../coding-convention/C.md](../coding-convention/C.md);
> the canonical source for language-agnostic quality is [../../.clauderules](../../.clauderules).

---

## Table of Contents

1. [Project Architecture](#1-project-architecture)
2. [File Organization](#2-file-organization)
3. [Naming Conventions](#3-naming-conventions)
4. [Common Type Definitions](#4-common-type-definitions)
5. [Data Structure Definitions](#5-data-structure-definitions)
6. [Macro Patterns](#6-macro-patterns)
7. [Function Structure](#7-function-structure)
8. [BSP Hardware Abstraction](#8-bsp-hardware-abstraction)
9. [Error Handling Patterns](#9-error-handling-patterns)
10. [Memory Management](#10-memory-management)
11. [Comment Style](#11-comment-style)
12. [Code Formatting](#12-code-formatting)
13. [Protocol Communication Structure](#13-protocol-communication-structure)
14. [Timing Management](#14-timing-management)

---

## 1. Project Architecture

Follows a 4-tier layered structure.

```
Core/            → main.c, RTOS, interrupt handlers
Include/BSP/     → GPIO, I2C, SPI, UART, ADC, TIMER (HAL wrappers)
Include/DRIVERS/ → sensor/peripheral drivers
Include/APP/     → PROC, SERVER_IF, SENSOR_IF
```

**Dependency direction:** `APP → DRIVERS → BSP → HAL`

- Higher layers call lower layers.
- Reverse dependencies are forbidden.
- HAL functions must be called only through BSP wrappers.

---

## 2. File Organization

### Header Guard

```c
#ifndef _FILENAME_H_
#define _FILENAME_H_

// ...

#endif
```

Format: `_FILENAME_H_` (all uppercase, leading/trailing underscores)
`#pragma once` is not used.

---

### Extern Variable Guard Pattern

Every module manages externs with this pattern.

**Header file (I2C.h)**
```c
#ifdef _I2C_C_
    #define I2C_EXT
#else
    #define I2C_EXT extern
#endif

I2C_EXT void    I2C_INIT(void);
I2C_EXT void    I2C_SEND(I2C_CH ch, uint16_t DeviceAdd, uint8_t* data, uint8_t len);
I2C_EXT uint8_t I2C_RECV(I2C_CH ch, uint16_t DeviceAdd, uint8_t* data, uint8_t len);
```

**Implementation file (I2C.c)**
```c
#define _I2C_C_
  #include "I2C.h"
#undef  _I2C_C_
```

- Defining `_MODULE_C_` in the implementation file makes `MODULE_EXT` an empty string, so it becomes a definition.
- When other files include it, `MODULE_EXT` becomes `extern`, so it becomes a declaration.

---

### Include Order

```c
// 1. Standard C library
#include <stdio.h>
#include <string.h>

// 2. Vendor HAL
#include "{{MCU_HAL_HEADER}}"

// 3. RTOS
#include "cmsis_os.h"
#include "FreeRTOS.h"

// 4. Project common (types, macros)
#include "default.h"
#include "util.h"

// 5. BSP layer
#include "GPIO.h"
#include "I2C.h"
#include "UART.h"

// 6. DRIVERS layer
#include "RS485.h"

// 7. APP layer
#include "PROC.h"
#include "SENSOR_IF.h"
```

---

## 3. Naming Conventions

Naming conventions follow the project's central rules.
For detailed naming rules, see the following document:
👉 [C Coding Convention (`../coding-convention/C.md`)](../coding-convention/C.md)

---

## 4. Common Type Definitions

Use the types defined in `default.h`. They may be mixed with HAL types (`uint8_t`, etc.), but the project-defined types take precedence.

```c
typedef unsigned char           UINT8;
typedef signed char             INT8;
typedef unsigned short          UINT16;
typedef signed short            INT16;
typedef unsigned long           UINT32;
typedef signed long             INT32;
```

---

## 5. Data Structure Definitions

### Packed Struct (protocol packets, communication data)

```c
typedef __packed struct {
    uint8_t  STX;
    uint8_t  LEN;
    uint8_t  ID;
    uint8_t  CLASS;
    uint8_t  FUNC;
    uint8_t  PARAM0;
    uint8_t  PARAM1;
    uint8_t  DATA[PROTOCOL_SIZE];
    uint16_t CRC16;
    uint8_t  ETX;
} SCOMM;
```

- Communication packet and hardware register map structs must use `__packed`
- Prevents data corruption caused by padding

---

### Bitfield Union (hardware registers)

```c
typedef __packed union {
    struct {
        uint8_t FLAG : 1;    // (LSB)
        uint8_t ADDR : 7;    // (MSB)
    };
    uint8_t val;
} UREG_ADDR;
```

- Access the whole byte via `val`
- Access individual fields via bit fields
- LSB/MSB comments are required

---

## 6. Macro Patterns

### Unit Macros

```c
#define MHZ     *1000000l
#define KHZ     *1000l
#define HZ      *1l

// Usage: 16 MHZ → automatically 16000000
uint32_t clk = 16 MHZ;
```

---

### Bit-Operation Macros

```c
#define SWAP16(A)    ((((A << 8 ) & 0xFF00)) | ((A >> 8) & 0x00FF))
#define UINT16_H(x)  ( (UINT8)(x >>  8) & (0xFF) )
#define UINT16_L(x)  ( (UINT8)(x >>  0) & (0xFF) )
#define NTOHS(x)     (((x<<8) & 0xFF00) | ((x>>8) & 0x00FF))
#define HTONS(x)     NTOHS(x)
```

---

### Configuration Constant Macros

```c
#define SENSOR_TIMEOUT              (100)
#define SENSOR_PWR_REBOOT_TIMEOUT   (1000)
#define SENSOR_RETRY                (10)
#define PROTOCOL_SIZE               (50)
```

- Do not use magic numbers directly.
- Define all configuration values as macro constants.

---

## 7. Function Structure

### Function Declaration (header file - column-aligned)

Align the return types and function names of related functions in columns.

```c
I2C_EXT void     I2C_INIT(void);
I2C_EXT void     I2C_SEND(I2C_CH ch, uint16_t DeviceAdd, uint8_t* data, uint8_t len);
I2C_EXT uint8_t  I2C_RECV(I2C_CH ch, uint16_t DeviceAdd, uint8_t* data, uint8_t len);
```

---

### Function Definition (implementation file - brace on a new line)

```c
void I2C_INIT(void)
{
    I2C1_Init();
    I2C2_Init();
}
```

---

### Section Divider Comments

Separate the external/internal function areas within the implementation file.

```c
/******************************************     Extern Function*/

void I2C_INIT(void) { ... }
void I2C_SEND(...) { ... }

/******************************************     Static Function*/

static void I2C1_Init(void) { ... }
static void I2C2_Init(void) { ... }
```

---

## 8. BSP Hardware Abstraction

### Channel Enum Selection

Use an enum instead of a channel number. Direct use of magic numbers is forbidden.

```c
typedef enum { i2c1 = 0, i2c2 } I2C_CH;
typedef enum { uart2 = 0, uart3, uart4 } UART_CH;
```

---

### HAL Wrapper Function Pattern

The APP/DRIVERS layers do not call the HAL directly. They must call it through a BSP function.

```c
void I2C_SEND(I2C_CH ch, uint16_t DeviceAdd, uint8_t* data, uint8_t len)
{
    switch(ch)
    {
    case i2c1 : HAL_I2C_Master_Transmit(&hi2c1, DeviceAdd, data, len, 10); break;
    case i2c2 : HAL_I2C_Master_Transmit(&hi2c2, DeviceAdd, data, len, 10); break;
    default   : break;
    }
}
```

---

## 9. Error Handling Patterns

### Boolean Return

Return success/failure as `uint8_t`. `0 = false`, `1 = true`.

```c
static uint8_t READ_SENSOR(uint8_t CMD)
{
    uint8_t ret = false;

    // I2C transmit and receive, CRC verification
    // ...
    if (crc8(&rxbuf[0]) == rxbuf[2]) {
        ret = true;
    }
    return ret;
}
```

---

### Timeout + Retry + Power-Cycling Pattern

```c
if (sAtt_CH1.fTrans) {
    if (tCH1_TO++ > SENSOR_TIMEOUT) {
        SENSOR_CH1_STATUS();       // reset state
        tCH1_TO = 0;
        if (++tCH1_RETRY > SENSOR_RETRY) {
            SENSOR_CH1_PWR_CTRL(eP_OFF);  // force recovery via power cycling
        }
    }
}
```

- Step 1: monitor the timeout counter
- Step 2: on timeout, reset state and retry
- Step 3: on exceeding the retry count, power-cycle

---

### CRC Verification Pattern

Communication data must be processed only after CRC verification.

```c
// CRC-8 (sensor data)
if (crc8(&rxbuf[0]) == rxbuf[2]) { /* valid */ }

// CRC-16 Modbus (protocol packet)
if (packet.CRC16 == calc_crc16(packet)) { /* valid */ }
```

---

## 10. Memory Management

### No Dynamic Allocation

Use of `malloc()`, `free()`, `calloc()`, `realloc()` is forbidden.
Every buffer must have its size determined at compile time.

```c
// Correct: static fixed-size array
static uint32_t u32AdcSamples[NUM_OF_AVG];
static uint8_t  i2cRxBuf[16];

// Forbidden: dynamic allocation
uint8_t* buf = malloc(size);  // never use
```

---

### Define Buffer Sizes as Macros

```c
#define PROTOCOL_SIZE   (50)
#define NUM_OF_AVG      (100)

uint8_t DATA[PROTOCOL_SIZE];
uint32_t samples[NUM_OF_AVG];
```

---

### UART Buffering - Queue Pattern

```c
// Initialize
Q_Clear(&qTX_U2);  Q_Clear(&qRX_U2);

// Use
Q_Push(&qTX_U2, data);
Q_Pop(&qRX_U2, &data);
```

---

### Parallel State Management for Multiple Channels

Manage the state variables of multiple sensor channels independently per channel.

```c
// Externally shared variables
SERIAL_EXT SerialAttribute sAtt_CH1;
SERIAL_EXT SerialAttribute sAtt_CH2;

// Per-channel timer counters (static)
static uint32_t tCH1_TO, tCH1_RETRY;
static uint32_t tCH2_TO, tCH2_RETRY;
```

---

## 11. Comment Style

### Section Dividers

Separate sections with 40 or more `*` characters. Maintain the existing codebase's notation.

```c
/******************************************     Extern Function*/

/******************************************     Static Function*/
```

---

### Function Doxygen Comments

Write Doxygen-format comments on externally public functions.

```c
/**
  * @brief  Transmit data over an I2C channel
  * @param  ch         I2C channel (i2c1 / i2c2)
  * @param  DeviceAdd  Slave device address
  * @param  data       Pointer to the data to transmit
  * @param  len        Length of the data to transmit
  * @retval None
  */
void I2C_SEND(I2C_CH ch, uint16_t DeviceAdd, uint8_t* data, uint8_t len)
```

---

### File Header Comment

```c
/**
  * @file    I2C.c
  * @brief   I2C BSP Layer - HAL wrapper for I2C1, I2C2
  */
```

---

## 12. Code Formatting

### Indentation

Use tabs. Do not mix spaces.

### Brace Style

```c
// Function definition: brace on a new line
void SENSOR_PROC(void)
{
    // body
}

// Control statement: brace on the same line
if (condition) {
    // body
}

// switch: brace on the same line
switch(ch)
{
case i2c1 : ...; break;
case i2c2 : ...; break;
default   : break;
}
```

---

## 13. Protocol Communication Structure

### Binary Packet Frame

```
┌─────┬─────┬────┬───────┬──────┬────────┬────────┬──────────────┬───────┬─────┐
│ STX │ LEN │ ID │ CLASS │ FUNC │ PARAM0 │ PARAM1 │  DATA[0..49] │ CRC16 │ ETX │
│0x02 │  1B │ 1B │  1B   │  1B  │   1B   │   1B   │    50 Bytes  │  2B   │0x03 │
└─────┴─────┴────┴───────┴──────┴────────┴────────┴──────────────┴───────┴─────┘
```

| Field | Value | Description |
|------|-----|------|
| STX | `0x02` | Packet start |
| LEN | variable | Data length |
| ID | `0x00~0x0F` | Device ID |
| CLASS | `'S'/'G'/'D'` | Set/Get/Data |
| CRC16 | Modbus CRC | Integrity check |
| ETX | `0x03` | Packet end |

---

### State-Machine-Based Parser

Implement with byte-by-byte sequential parsing.

```c
typedef enum {
    eP_STX = 0, eP_LEN, eP_ID, eP_CLASS, eP_FUNC,
    eP_PARAM0, eP_PARAM1, eP_DATA, eP_CRC, eP_ETX
} EPARSE_STATE;

uint8_t Serial_Parse(SerialAttribute* p, uint8_t data)
{
    switch(p->state)
    {
    case eP_STX:
        if (data == PROTOCOL_STX) {
            p->state = eP_LEN;
        }
        break;
    case eP_LEN:
        p->packet.LEN = data;
        p->state = eP_ID;
        break;
    // ...
    case eP_ETX:
        if (data == PROTOCOL_ETX) {
            return true;  // complete packet received
        }
        break;
    }
    return false;
}
```

---

### CRC Verification Required

Received packets must be processed only after CRC verification.

```c
if (Serial_Parse(&sAtt_CH1, rxByte)) {
    if (sAtt_CH1.packet.CRC16 == calc_crc16(&sAtt_CH1.packet)) {
        SENSOR_IF_PROC(&sAtt_CH1);  // process after passing verification
    }
}
```

---

## 14. Timing Management

### Global Tick Variables

Use project-defined tick variables instead of `HAL_GetTick()`.

```c
PROC_EXT uint32_t tick_1m;            // 1ms counter (SysTick-based)
PROC_EXT uint32_t tick_1m_timeout;    // for timeout comparison
PROC_EXT uint32_t ostick_1s;          // 1-second counter
```

---

### SysTick-Based Periodic Function Calls

```c
void SysTick_Handler(void)
{
    HAL_IncTick();
    osSystickHandler();
    PROC_TIMER();   // called every 1ms
}
```

---

### Timeout Pattern

```c
static uint32_t tCH1_TO = 0;

void SENSOR_TASK(void)
{
    // assumed to be called every 1ms
    if (tCH1_TO++ > SENSOR_TIMEOUT) {  // SENSOR_TIMEOUT = 100 → 100ms
        tCH1_TO = 0;
        // timeout handling
    }
}
```

---

## Key Summary

| Rule | Content |
|------|------|
| **Function name** | `ALL_CAPS_UNDERSCORE` (public), `snake_case` (internal) |
| **Enum type** | `E` prefix (e.g. `ESENSOR_STATUS`) |
| **Enum value** | `e` prefix (e.g. `eP_OFF`) |
| **Struct** | `S` prefix (e.g. `SCOMM`) |
| **Union** | `U` prefix (e.g. `UREG_ADDR`) |
| **Extern management** | Mandatory `#ifdef _MODULE_C_` pattern |
| **Dynamic memory** | **Forbidden** (malloc/free not allowed) |
| **Direct HAL calls** | **Forbidden** (must use the BSP wrapper) |
| **Error handling** | boolean return + timeout/retry/power-cycling |
| **Architecture** | Core → BSP → DRIVERS → APP one-way dependency |
| **Braces** | function on a new line, control statement on the same line |
| **Indentation** | tabs |
| **CRC verification** | mandatory before processing a received packet |
| **Buffer size** | defined as a macro constant; no magic numbers |
