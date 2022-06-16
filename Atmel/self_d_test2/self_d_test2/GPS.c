/*
 * GPS.c
 *
 * Created: 2022-05-11 오후 9:34:08
 * Author : LEEHUIDO
 */ 
#define _CRT_SECURE_NO_WARNINGS    // strcpy 보안 경고로 인한 컴파일 에러 방지
#define F_CPU 16000000UL

#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include "GPS.h"
#include "UART.h"

unsigned char uart2_rx_idx = 0;
char uart2_rx_buffer[255];

unsigned char uart2_rx_data;
unsigned char uart2_rx_flag =0;
unsigned char uart2_rx_str_flag =0;

ISR(USART2_RX_vect)	// 어떤 인터럽트가 발생했을 때 이를 받아서 처리하는 함수를 ISR함수
{
	uart2_rx_buffer[uart2_rx_idx++] = UDR2;
	
	if(uart2_rx_buffer[(uart2_rx_idx-1)] == '\n'){
		uart2_rx_buffer[(uart2_rx_idx)] = NULL;
		uart2_rx_idx=0;
		uart2_rx_str_flag = 1;
	}
	else if(uart2_rx_idx>=254){
		uart2_rx_idx=0;
	}
}

void GPS_UART2_init(long baud)
{
	unsigned short ubrr = (F_CPU/(8*baud))-1;	//보레이트를 결정하는 공식 (비동기 2배속 모드)
	UBRR2H = (unsigned char)(ubrr >> 8);
	UBRR2L = (unsigned char)ubrr;
	
	UCSR2A = (1 << U2X2);	//비동기 2배속 모드
	//	UCSR2A 레지스터는 USART2 포트의 송수신 동작을 송수신 상태를 저장하는 기능을 수행
	
	UCSR2B = (1 << RXCIE2) | (0 << TXCIE2) | (1 << RXEN2) | (0 << TXEN2);
	//	UCSR2B 레지스터는 USART2 포트의 송수신 동작을 제어
	//	RXCIE2, TXCIE2: 수신완료,송신완료 인터럽트를 개별적으로 허용하는 비트
	//	RXEN2, TXEN2: 송신 데이터, 수신 데이터 레지스터 준비완료 인터럽트를 개별적으로 허용하는 비트
	
	UCSR2C= (1 << UCSZ21) | (1 << UCSZ20);
	//	UCSR2C 레지스터는 USART0 포트의 송수신 동작을 제어하는 기능
	//	UCSZ21: 전송 문자의 데이터 비트수를 설정 (8비트로 설정됨)
	//	Asynchronous USART, Parity Disable, 1 Stop-bit, 8-bit data
}

unsigned char GPS_UART2_getchar(char *c)
{
	if(uart2_rx_flag){
		*c = uart2_rx_buffer[(uart2_rx_idx-1)];
		uart2_rx_flag = 0;
		return 1;
	}
	else{
		return 0;
	}
}

char GPS_UART2_gets(void)
{
	if(uart2_rx_str_flag){
		uart2_rx_str_flag = 0;
		return 1;
	}
	else{
		return 0;
	}
}

char GPS_parsing(char *s)
{
	unsigned char bChecksum = 0;
	unsigned char asterisk_idx = 0;
	
	if(GPS_UART2_gets()==0){
		return -1;
	}

	if(!(uart2_rx_buffer[0]=='$'&&uart2_rx_buffer[3]=='R'&&uart2_rx_buffer[4]=='M'&&uart2_rx_buffer[5]=='C')){
		return -1;
	}

	for(unsigned char i=1;  uart2_rx_buffer[i]!='*'; i++){
		bChecksum ^= uart2_rx_buffer[i];
		asterisk_idx=i;
	}

	if(bChecksum!=((atohex(uart2_rx_buffer[asterisk_idx+2])*16)+ atohex(uart2_rx_buffer[asterisk_idx+3]))){
		printf("GPS Packet Error\n");
		return -2;
	}

	if(uart2_rx_buffer[18] != 'A'){
		printf("Wait GPS not found\n");
		return -2;
	}

	strcpy(s, uart2_rx_buffer);
	return 1;
}

unsigned char atohex(char hexadecimal)
{
	int decimal = 0;
	if(hexadecimal>='A' && hexadecimal<='F'){
		decimal = decimal*16 + hexadecimal-'A'+10;
	}
	else if(hexadecimal>='a' && hexadecimal<='f'){
		decimal = decimal*16 + hexadecimal-'a'+10;	
	}
	else if(hexadecimal>='0' && hexadecimal<='9'){
		decimal = decimal*16 + hexadecimal-'0';			
	}
	return decimal;
}

long atoi_(char*s)
{
	long temp = 0;
	for (char i = 0; i < strlen(s); i++)
	{
		if (s[i] == '.') {
			continue;
		}
		temp = temp * 10 + (long)(s[i] - '0');
	}
	return temp;
}