/*
 * Timer.c
 *
 * Created: 2022-05-27 오전 10:20:02
 *  Author: j3jjj
 */ 
#define F_CPU 16000000UL

#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/atomic.h>
#include <limits.h>
#include "Timer.h"

int Timer0_1ms_cnt =0;
int Timer0_1ms_flag =0;

int Timer0_20ms_cnt =0;
int Timer0_20ms_flag =0;

int Timer0_240ms_cnt =0;
int Timer0_240ms_flag =0;

int Timer0_500ms_cnt =0;
int Timer0_500ms_flag =0;

int Timer0_1000ms_cnt =0;
int Timer0_1000ms_flag =0;

ISR(TIMER0_OVF_vect)
{
	if(++Timer0_1ms_cnt ==1)
	{
		Timer0_1ms_cnt =0;
		Timer0_1ms_flag =1;
	}
	if(++Timer0_20ms_cnt ==20)
	{
		Timer0_20ms_cnt =0;
		Timer0_20ms_flag =1;
	}
	if(++Timer0_240ms_cnt ==240)
	{
		Timer0_240ms_cnt =0;
		Timer0_240ms_flag =1;
	}	
	if(++Timer0_500ms_cnt ==500)
	{
		Timer0_500ms_cnt =0;
		Timer0_500ms_flag =1;
	}	
	if(++Timer0_1000ms_cnt ==1000)
	{
		Timer0_1000ms_cnt =0;
		Timer0_1000ms_flag =1;
	}	
	TCNT0 = 6;
}

void Timer0_init(void)
{
	TCCR0A = 0x00;
	//  Compare Output Mode, non-PWM, Set on Normal port operation, 분주율 64	
	
	TCCR0B = (1 << CS01) | (1 << CS00);
	//  분주율 64
	
	TIMSK0 |= (1 << TOIE0);
}

int Timer0_flag(int ms)
{
	if(ms ==1)
	{
		if(Timer0_1ms_flag ==1)
		{
			Timer0_1ms_flag =0;
			return 1;
		}
	}
	if(ms == 20)
	{
		if(Timer0_20ms_flag ==1)
		{
			Timer0_20ms_flag =0;
			return 1;
		}
	}
	if(ms == 240)
	{
		if(Timer0_240ms_flag ==1)
		{
			Timer0_240ms_flag =0;
			return 1;
		}
	}	
	if(ms == 500)
	{
		if(Timer0_500ms_flag ==1)
		{
			Timer0_500ms_flag =0;
			return 1;
		}
	}	
	if(ms == 1000)
	{
		if(Timer0_1000ms_flag == 1)
		{
			Timer0_1000ms_flag =0;
			return 1;
		}
	}	
	return 0;
}