/*
 * XM430.h
 *
 * Created: 2022-05-11 오후 3:21:30
 * Author : LEEHUIDO
 */ 
#ifndef XM430_h
#define XM430_h

typedef unsigned char byte;

void XM430_init(long baud);
void xm430_transmit(unsigned char data);
void TxPacket_xm430(byte bID,byte blnstruction,byte bParameterLength);
void xm430_position(unsigned char ID_number, float p_number);
unsigned short update_crc(unsigned short crc_accum, unsigned char *data_blk_ptr, unsigned short data_blk_size);
void xm430_ID(unsigned char ID_number);
void xm430_MODE(unsigned char ID_numbe);
void xm430_Torque(unsigned char ID_number, unsigned char Torque);
void xm430_Velocity_limit(unsigned char ID_number, unsigned int Velocity_limit);
void xm430_Goal_velocity(unsigned char ID_number, int32_t velocity);
void xm430_Goal_velocity_action(unsigned char ID_number_0, unsigned char ID_number_1, int32_t velocity_0, int32_t velocity_1);
#endif