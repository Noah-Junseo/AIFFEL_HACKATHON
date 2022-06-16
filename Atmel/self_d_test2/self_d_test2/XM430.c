/*
 * XM430.c
 *
 * Created: 2022-05-11 오후 3:21:22
 * Author : LEEHUIDO
 */ 
#define F_CPU 16000000UL

#include <avr/io.h>
#include <stdio.h>
#include <stdint.h>
#include <util/delay.h>
#include "XM430.h"

#define sbi(REG8,BITNUM) REG8 |= _BV(BITNUM)
#define CHECK_TXD1_FINISH bit_is_set(UCSR1A,6)				//UCSR1A의 6비트는 송신을 다했으면 1
#define Torque_ON  _delay_ms(300); xm430_Torque(0xFE, 1); _delay_ms(300);
#define Torque_OFF _delay_ms(300); xm430_Torque(0xFE, 0); _delay_ms(300);

byte gbpTxBuffer[128];
byte gbpParameter[128];

void XM430_init(long baud)
{	
	unsigned short ubrr = (F_CPU/(8*baud))-1;	//보레이트를 결정하는 공식 (비동기 2배속 모드)
	UBRR1H = (unsigned char)(ubrr >> 8);
	UBRR1L = (unsigned char)ubrr;
	
	UCSR1A = (1 << U2X1);	//비동기 2배속 모드
	//	UCSR1A 레지스터는 USART1 포트의 송수신 동작을 송수신 상태를 저장하는 기능을 수행

	UCSR1B = (1 << TXEN1);
	//	UCSR1B 레지스터는 USART1 포트의 송수신 동작을 제어
	//	TXEN1: 송신 데이터 레지스터 준비완료 인터럽트를 개별적으로 허용하는 비트

	UCSR1C= (1 << UCSZ01) | (1 << UCSZ00);
	//	UCSR0C 레지스터는 USART0 포트의 송수신 동작을 제어하는 기능
	//	UCSZ01: 전송 문자의 데이터 비트수를 설정 (8비트로 설정됨)
	//	Asynchronous USART, Parity Disable, 1 Stop-bit, 8-bit data
}

void xm430_transmit(unsigned char data)
{
	while(!(UCSR1A & (1<<UDRE1)));		
	//	UDRE1 = 5  , 레지스터 UCSR1A의 5비트는 자동(전송준비가 되면 1이된다)
	
	UDR1=data;
}

void TxPacket_xm430(byte bID,byte blnstruction,byte bParameterLength)	//ID값,Instruction,parameter 길이
{
	byte bCount,bPacketLength;
	unsigned short bCRC;

	gbpTxBuffer[0] = 0xff;				//패킷의 시작을 알리는 신호
	gbpTxBuffer[1] = 0xff;				//패킷의 시작을 알리는 신호
	gbpTxBuffer[2] = 0xfd;				//패킷의 시작을 알리는 신호
	gbpTxBuffer[3] = 0x00;				//Reserved(Header와 동일한 기능)
	gbpTxBuffer[4] = bID;				//ID
	gbpTxBuffer[5] = ((bParameterLength+3) & 0xff);			//패킷의 길이  (Parameter0(1) + ParameterN(N) Parameter 개수(N) Instruction(1) + 2) 하위 비트
	gbpTxBuffer[6] = (((bParameterLength+3)>>8) & 0xff);	//패킷의 길이  (Parameter0(1) + ParameterN(N) Parameter 개수(N) Instruction(1) + 2) 상위 비트
	gbpTxBuffer[7] = blnstruction;		//Dynamixel에게 수행하라고 지시하는 명령.
	
	for(bCount = 8; bCount < (bParameterLength+8); bCount++)		//Put gbpParameter Value in gbpTxBuffer
	{
		gbpTxBuffer[bCount] = gbpParameter[bCount-8];
	}

	//CRC
	//Packet이 통신 중에 파손되었는지를 점검하기 위한 필드 (16bit CRC)
	//하위 바이트와 상위 바이트를 Instruction Packet에서 나누어서 보냄.
	//CRC 계산 범위: Instruction Packet의 Header (FF FF FD 00)를 포함하여, CRC 필드 이전까지.
	bPacketLength = bParameterLength+8;			//Header(3) + Reserved(1) + Packet ID(1) + Length(2) + 패킷의 길이 - CRC(2) = 패킷의 길이 + 5 = (bParameterLength+3) + 5 = bParameterLength + 8
	bCRC = update_crc(0, gbpTxBuffer, bPacketLength);
	gbpTxBuffer[bCount] = (bCRC & 0xFF);
	gbpTxBuffer[bCount+1] = (bCRC>>8) & 0xFF;
	
	_delay_ms(1);
	for(bCount=0;bCount<(bPacketLength+2);bCount++)	//uart통신 Packet 전송
	{
		sbi(UCSR1A,6);
		xm430_transmit(gbpTxBuffer[bCount]);
//		UART0_putchar(gbpTxBuffer[bCount]);
	}
	while(!CHECK_TXD1_FINISH);		//전송이 끝날때 까지 대기
	_delay_ms(1);
//	return(bPacketLength);		//Packet길이 반환
}

unsigned short update_crc(unsigned short crc_accum, unsigned char *data_blk_ptr, unsigned short data_blk_size)
{
	/*
	리턴 값 : 16bit CRC 값
	crc_accum : ‘0’으로 설정
	data_blk_ptr : Packet array pointer
	data_blk_size : CRC를 제외한 패킷의 byte 수
	data_blk_size = Header(3) + Reserved(1) + Packet ID(1) + Length(2) + Length - CRC(2) = 3 + 1 + 1 + 2 + Length - 2 = 5 + Length;
	Packet Length = (LEN_H « 8 ) + LEN_L; //Little-endian
	*/
	unsigned short i, j;
	unsigned short crc_table[256] = {
		0x0000, 0x8005, 0x800F, 0x000A, 0x801B, 0x001E, 0x0014, 0x8011,
		0x8033, 0x0036, 0x003C, 0x8039, 0x0028, 0x802D, 0x8027, 0x0022,
		0x8063, 0x0066, 0x006C, 0x8069, 0x0078, 0x807D, 0x8077, 0x0072,
		0x0050, 0x8055, 0x805F, 0x005A, 0x804B, 0x004E, 0x0044, 0x8041,
		0x80C3, 0x00C6, 0x00CC, 0x80C9, 0x00D8, 0x80DD, 0x80D7, 0x00D2,
		0x00F0, 0x80F5, 0x80FF, 0x00FA, 0x80EB, 0x00EE, 0x00E4, 0x80E1,
		0x00A0, 0x80A5, 0x80AF, 0x00AA, 0x80BB, 0x00BE, 0x00B4, 0x80B1,
		0x8093, 0x0096, 0x009C, 0x8099, 0x0088, 0x808D, 0x8087, 0x0082,
		0x8183, 0x0186, 0x018C, 0x8189, 0x0198, 0x819D, 0x8197, 0x0192,
		0x01B0, 0x81B5, 0x81BF, 0x01BA, 0x81AB, 0x01AE, 0x01A4, 0x81A1,
		0x01E0, 0x81E5, 0x81EF, 0x01EA, 0x81FB, 0x01FE, 0x01F4, 0x81F1,
		0x81D3, 0x01D6, 0x01DC, 0x81D9, 0x01C8, 0x81CD, 0x81C7, 0x01C2,
		0x0140, 0x8145, 0x814F, 0x014A, 0x815B, 0x015E, 0x0154, 0x8151,
		0x8173, 0x0176, 0x017C, 0x8179, 0x0168, 0x816D, 0x8167, 0x0162,
		0x8123, 0x0126, 0x012C, 0x8129, 0x0138, 0x813D, 0x8137, 0x0132,
		0x0110, 0x8115, 0x811F, 0x011A, 0x810B, 0x010E, 0x0104, 0x8101,
		0x8303, 0x0306, 0x030C, 0x8309, 0x0318, 0x831D, 0x8317, 0x0312,
		0x0330, 0x8335, 0x833F, 0x033A, 0x832B, 0x032E, 0x0324, 0x8321,
		0x0360, 0x8365, 0x836F, 0x036A, 0x837B, 0x037E, 0x0374, 0x8371,
		0x8353, 0x0356, 0x035C, 0x8359, 0x0348, 0x834D, 0x8347, 0x0342,
		0x03C0, 0x83C5, 0x83CF, 0x03CA, 0x83DB, 0x03DE, 0x03D4, 0x83D1,
		0x83F3, 0x03F6, 0x03FC, 0x83F9, 0x03E8, 0x83ED, 0x83E7, 0x03E2,
		0x83A3, 0x03A6, 0x03AC, 0x83A9, 0x03B8, 0x83BD, 0x83B7, 0x03B2,
		0x0390, 0x8395, 0x839F, 0x039A, 0x838B, 0x038E, 0x0384, 0x8381,
		0x0280, 0x8285, 0x828F, 0x028A, 0x829B, 0x029E, 0x0294, 0x8291,
		0x82B3, 0x02B6, 0x02BC, 0x82B9, 0x02A8, 0x82AD, 0x82A7, 0x02A2,
		0x82E3, 0x02E6, 0x02EC, 0x82E9, 0x02F8, 0x82FD, 0x82F7, 0x02F2,
		0x02D0, 0x82D5, 0x82DF, 0x02DA, 0x82CB, 0x02CE, 0x02C4, 0x82C1,
		0x8243, 0x0246, 0x024C, 0x8249, 0x0258, 0x825D, 0x8257, 0x0252,
		0x0270, 0x8275, 0x827F, 0x027A, 0x826B, 0x026E, 0x0264, 0x8261,
		0x0220, 0x8225, 0x822F, 0x022A, 0x823B, 0x023E, 0x0234, 0x8231,
		0x8213, 0x0216, 0x021C, 0x8219, 0x0208, 0x820D, 0x8207, 0x0202
	};

	for(j = 0; j < data_blk_size; j++)
	{
		i = ((unsigned short)(crc_accum >> 8) ^ data_blk_ptr[j]) & 0xFF;
		crc_accum = (crc_accum << 8) ^ crc_table[i];
	}

	return crc_accum;
}

void xm430_position(unsigned char ID_number, float p_number)			//모터 위치값,모터 ID값
{
	unsigned int position = 11.375*p_number;	//Change 0~360 to 0~4095
	
	gbpParameter[0] = 0x74; //goal position address_L
	gbpParameter[1] = (0x74>>8); //goal position address_H
	gbpParameter[2] = (unsigned char)(position); //Writing Data  , goal position
	gbpParameter[3] = (unsigned char)(position>>8); //goal position
	gbpParameter[4] = (unsigned char)(position>>16); //goal position
	gbpParameter[5] = (unsigned char)(position>>24); //goal position

	TxPacket_xm430(ID_number, 0x03, 0x06);	// , 0x03명령, 길이
}

void xm430_ID(unsigned char ID_number)		//ID설정 함수
{
	Torque_OFF
	gbpParameter[0] = 0x07;				//ID address_L
	gbpParameter[1] = 0x00;				//ID address_H
	gbpParameter[2] = ID_number;
	
	TxPacket_xm430(0xFE, 0x03, 0x03);
	Torque_ON
}

void xm430_Torque(unsigned char ID_number, unsigned char Torque)		//TORQUE 설정 함수
{
	//1이면 ON
	//0이면 OFF(EEPROM할 때 0으로 설정해야함)
	gbpParameter[0] = 0x40;				//TORQUE address_L
	gbpParameter[1] = (0x40>>8);		//TORQUE address_H
	gbpParameter[2] = Torque;
	
	TxPacket_xm430(ID_number, 0x03, 0x03);
}

void xm430_Velocity_limit(unsigned char ID_number, unsigned int Velocity_limit)		//Velocity limit 설정 함수
{
	//기본값(330, 0.229[rev/min]) 0~1023
	Torque_OFF
	gbpParameter[0] = 0x2c;				//Velocity_limit address_L
	gbpParameter[1] = (0x2c>>8);		//Velocity_limit address_H
	gbpParameter[2] = (unsigned char)(Velocity_limit); //Writing Data  , Velocity_limit
	gbpParameter[3] = (unsigned char)(Velocity_limit>>8); //Velocity_limit
	gbpParameter[4] = (unsigned char)(Velocity_limit>>16); //Velocity_limit
	gbpParameter[5] = (unsigned char)(Velocity_limit>>24); //Velocity_limit
	
	TxPacket_xm430(ID_number, 0x03, 0x06);
	Torque_ON
}

void xm430_Operating_mode(unsigned char ID_number, unsigned char Operating_mode)		//Operating mode 설정 함수
{
	//Operating Mode 0~16(기본값: 3)
	//0: 전류제어 모드
	//1: 속도제어 모드
	//3: 위치제어 모드
	//4: 확장 위치제어 모드(Multi-turn)
	//5: 전류기반 위치제어 모드
	//16:PWM 제어 모드 (Voltage Control Mode)
	
	Torque_OFF
	gbpParameter[0] = 0x0B;				//Operating mode address_L
	gbpParameter[1] = (0x0B>>8);		//Operating mode address_H
	gbpParameter[2] = Operating_mode;
	
	TxPacket_xm430(ID_number, 0x03, 0x03);
	Torque_ON
}
void xm430_Goal_velocity(unsigned char ID_number, int32_t velocity)
{
	if(velocity<0){
		velocity = ~(velocity*(-1)) +1;
	}
	gbpParameter[0] = 0x68;				//Goal_velocity address_L
	gbpParameter[1] = (0x68>>8);		//Goal_velocity address_H
	gbpParameter[2] = (unsigned char)(velocity); //Writing Data  , Goal velocity
	gbpParameter[3] = (unsigned char)(velocity>>8); //Writing Data  , Goal velocity
	gbpParameter[4] = (unsigned char)(velocity>>16); //Writing Data  , Goal velocity
	gbpParameter[5] = (unsigned char)(velocity>>24); //Writing Data  , Goal velocity

	TxPacket_xm430(ID_number, 0x03, 0x06);
}

void xm430_Goal_velocity_action(unsigned char ID_number_0, unsigned char ID_number_1, int32_t velocity_0, int32_t velocity_1)
{
	//ID num_1, ID num_1 속도, ID num_2, ID num_2 속도	
	xm430_Goal_velocity(ID_number_0, velocity_0);
	xm430_Goal_velocity(ID_number_1, (-1)*velocity_1);
	
	/*
	unsigned char temp_ID_num[2] = {ID_number_0, ID_number_1};
	int32_t temp_velocity[2] = {velocity_0, velocity_1};
	
	for(char i =0; i<2; i++){
		if (temp_velocity[i]<0){
			temp_velocity[i] = (-1)*temp_velocity[i];
			temp_velocity[i] = ~temp_velocity[i]+1;
		}
		gbpParameter[0] = 0x68;				//Goal_velocity address_L
		gbpParameter[1] = (0x68>>8);		//Goal_velocity address_H
		gbpParameter[2] = (unsigned char)(temp_velocity[i]); //Writing Data  , Goal velocity
		gbpParameter[3] = (unsigned char)(temp_velocity[i]>>8); //Writing Data  , Goal velocity
		gbpParameter[4] = (unsigned char)(temp_velocity[i]>>16); //Writing Data  , Goal velocity
		gbpParameter[5] = (unsigned char)(temp_velocity[i]>>24); //Writing Data  , Goal velocity
		TxPacket_xm430(temp_ID_num[i],0x04,6);
	}
	TxPacket_xm430(0xFE, 0x05, 0x00);
	*/
}