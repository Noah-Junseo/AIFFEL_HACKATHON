/*
 * UART.c
 *
 * Created: 2022-05-10 오전 11:13:54
 * Author : LEEHUIDO
 */ 
#define F_CPU 16000000UL

#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "UART.h"

static FILE mystdout = FDEV_SETUP_STREAM(UART0_p_putchar, NULL, _FDEV_SETUP_WRITE);
// FDEV_SETUP_STREAM은 매크로 함수이다. 즉 매크로 함수를 통해서 위 소스 코드에서 정의한 UART_putchar함수와 printf를 연결해주고 있다.

unsigned char uart0_rx_idx = 0;
unsigned char uart0_rx_data;
unsigned char uart0_rx_flag =0;
unsigned char uart0_rx_str_flag =0;

unsigned char UART0_TxBuffer[128];
unsigned char UART0_Rx_buffer[255];

ISR(USART0_RX_vect)	// 어떤 인터럽트가 발생했을 때 이를 받아서 처리하는 함수를 ISR함수
{
//	uart0_rx_data = UDR0;
//	UART0_Rx_buffer[uart0_rx_idx++] = uart0_rx_data;	
//	uart0_rx_flag = 1;
	UART0_Rx_buffer[uart0_rx_idx++] = UDR0;
	if(UART0_Rx_buffer[uart0_rx_idx-1] == '\n'){
		UART0_Rx_buffer[uart0_rx_idx] = NULL;
		uart0_rx_idx = 0;
		uart0_rx_str_flag = 1;
	}
	else if(uart0_rx_idx>=254){
		uart0_rx_idx=0;
	}
}

void UART0_init(long baud)
{
	unsigned short ubrr = (F_CPU/(8*baud))-1;	//보레이트를 결정하는 공식 (비동기 2배속 모드)
	UBRR0H = (unsigned char)(ubrr >> 8);
	UBRR0L = (unsigned char)ubrr;
	
	UCSR0A = (1 << U2X0);	//비동기 2배속 모드	
	//	UCSR0A 레지스터는 USART0 포트의 송수신 동작을 송수신 상태를 저장하는 기능을 수행
	
	UCSR0B = (1 << RXCIE0) | (0 << TXCIE0) | (1 << RXEN0) | (1 << TXEN0);
	//	UCSROB 레지스터는 USART0 포트의 송수신 동작을 제어	
	//	RXCIE0, TXCIE0: 수신완료,송신완료 인터럽트를 개별적으로 허용하는 비트
	//	RXEN0, TXEN0: 송신 데이터, 수신 데이터 레지스터 준비완료 인터럽트를 개별적으로 허용하는 비트
	
	UCSR0C= (1 << UCSZ01) | (1 << UCSZ00);
	//	UCSR0C 레지스터는 USART0 포트의 송수신 동작을 제어하는 기능
	//	UCSZ01: 전송 문자의 데이터 비트수를 설정 (8비트로 설정됨)
	//	Asynchronous USART, Parity Disable, 1 Stop-bit, 8-bit data
	
	stdout = &mystdout;
}

void UART0_putchar(unsigned char c)
{
	if(c == '\n') UART0_putchar('\r');
	while(!(UCSR0A &(1 << UDRE0)));
	UDR0 =c;
}

void UART0_p_putchar(unsigned char c, FILE * stream)
{
	if(c == '\n') UART0_p_putchar('\r', stream);
	while(!(UCSR0A &(1 << UDRE0)));
	UDR0 =c;
}

void UART0_puts(char *c)
{
	unsigned int i=0;
	while(1)
	{
		if(c[i] == NULL){
			break;
		}
		else{
			UART0_putchar(c[i++]);
		}
	}
}

unsigned char UART0_getchar(char *c)
{
	if(uart0_rx_flag){
		printf("flag\n");
		*c = uart0_rx_data;
		uart0_rx_flag = 0;
		return 1;
	}
	else{
		return 0;
	}
}

void UART0_GPS_send(char *s)
{
	unsigned char bChecksum = 0;
	unsigned char asterisk_idx = 0;
	unsigned char count = 0;

	for (unsigned char i = 0; i < strlen(s); i++) {
		if (s[i] == ',' && count == 8) {
			asterisk_idx = i;
			break;
		}
		else if (s[i] == ',') {
			count++;
		}
	}

	UART0_TxBuffer[0] = '$';

	for (unsigned char i = 20; i < asterisk_idx; i++) {
		if (i < 30) {
			UART0_TxBuffer[i - 19] = s[i];
		}
		else if (i > 30 && i < 43) {
			UART0_TxBuffer[i - 21] = s[i];
		}
		else if (i > 44) {
			UART0_TxBuffer[i - 21] = s[i];
		}
	}

	UART0_TxBuffer[asterisk_idx] = '*';

	for (unsigned char i = 1; UART0_TxBuffer[i] != '*'; i++) {
		bChecksum ^= UART0_TxBuffer[i];
	}
	UART0_TxBuffer[asterisk_idx + 1] = hex2ascii((int)(bChecksum / 16));
	UART0_TxBuffer[asterisk_idx + 2] = hex2ascii((int)(bChecksum % 16));
	UART0_TxBuffer[asterisk_idx + 3] = '\n';

	for (unsigned char i = 0; i < (asterisk_idx+4); i++) {
		printf("%c", UART0_TxBuffer[i]);
	}
}

void UART0_IMU_send(float _heading)
{
	char s[20];
	unsigned char bChecksum = 0;
	
	UART0_TxBuffer[0] = '@';
	itoa((int)(_heading*10), s, 10);

	for (unsigned char i = 0; i < strlen(s); i++) {
		
		UART0_TxBuffer[i+1] = s[i];
	}
	UART0_TxBuffer[strlen(s) + 1] = '*';

	for (unsigned char i = 1; UART0_TxBuffer[i] != '*'; i++) {
		bChecksum ^= UART0_TxBuffer[i];
	}
	UART0_TxBuffer[strlen(s) + 2] = hex2ascii((int)(bChecksum / 16));
	UART0_TxBuffer[strlen(s) + 3] = hex2ascii((int)(bChecksum % 16));
	UART0_TxBuffer[strlen(s) + 4] = '\n';

	for (unsigned char i = 0; i < (strlen(s) + 5); i++) {
		printf("%c", UART0_TxBuffer[i]);
	}
}

char hex2ascii(unsigned char a)
{
	if (a > 9) {
		return a + 0x37;
	}
	else {
		return a + 0x30;
	}
}

char UART0_gets(void)
{
	if(uart0_rx_str_flag){
		uart0_rx_str_flag = 0;
		return 1;
	}
	else{
		return 0;
	}
}

char UART0_parsing(char *s)
{
	unsigned char bChecksum = 0;
	unsigned char asterisk_idx = 0;
	
	if(UART0_gets()==0){
		return -1;
	}
	if((UART0_Rx_buffer[0]==0xFF&&UART0_Rx_buffer[1]==0xFF&&UART0_Rx_buffer[2]==0xFB&&UART0_Rx_buffer[6]=='*')){
		for(unsigned char i=0;  UART0_Rx_buffer[i]!='*'; i++){
			bChecksum ^= UART0_Rx_buffer[i];
			asterisk_idx=i;
		}

		if(bChecksum!=UART0_Rx_buffer[asterisk_idx+2]){
			printf("DATA Packet Error\n");
			return -2;
		}
		strcpy(s, UART0_Rx_buffer);		
		return 1;
	}
	if((UART0_Rx_buffer[0]==0xFF&&UART0_Rx_buffer[1]==0xFF&&UART0_Rx_buffer[2]==0xFD)){
		for(unsigned char i=0;  UART0_Rx_buffer[i]!='*'; i++){
			bChecksum ^= UART0_Rx_buffer[i];
			asterisk_idx=i;
		}
		if(bChecksum!=UART0_Rx_buffer[asterisk_idx+2]){
			printf("DATA Packet Error\n");
			return -2;
		}
		strcpy(s, UART0_Rx_buffer);
		return 2;
	}
}