#define F_CPU 16000000UL

#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>
#include <math.h>
#include "UART.h"
#include "twi.h"
#include "mpu9250.h"
#include "Timer.h"
#include "GPS.h"
#include "XM430.h"

int16_t accelCount[3];  // Stores the 16-bit signed accelerometer sensor output
int16_t gyroCount[3];   // Stores the 16-bit signed gyro sensor output
int16_t magCount[3];    // Stores the 16-bit signed magnetometer sensor output

float ax, ay, az, gx, gy, gz, mx, my, mz; // variables to hold latest sensor data values
float q[4] = {1.0f, 0.0f, 0.0f, 0.0f};    // vector to hold quaternion

char count = 0;
double pitch = 0, yaw = 0, roll = 0;

int main(void)
{
	DDRB = 0x80;
	sei();
	UART0_init(1000000);	// UART0 init
	GPS_UART2_init(9600);	
	XM430_init(57600);
	Timer0_init();
	twi_init();			// TWI init
	mpu9250_setup();	// MPU9250 init

	xm430_Torque(0xFE, 1);
    while (1)
    {
		char s[255];
		if (readByte(MPU9250_ADDRESS, INT_STATUS) & 0x01 && Timer0_flag(240)==1){
			readAccelData(accelCount);  // Read the x/y/z adc values
			getAres();
			// Now we'll calculate the accleration value into actual g's
			ax = (float)accelCount[0]*aRes; // - accelBias[0];  // get actual g value, this depends on scale being set
			ay = (float)accelCount[1]*aRes; // - accelBias[1]; 
			az = (float)accelCount[2]*aRes; // - accelBias[2];
			
			readGyroData(gyroCount);  // Read the x/y/z adc values
			getGres();
			// Calculate the gyro value into actual degrees per second
			gx = (float)gyroCount[0]*gRes;  // get actual gyro value, this depends on scale being set
   			gy = (float)gyroCount[1]*gRes;
   			gz = (float)gyroCount[2]*gRes;

   			readMagData(magCount);  // Read the x/y/z adc values
   			getMres();
   			mx = (float)magCount[0]*mRes*magCalibration[0] - magBias[0];  // get actual magnetometer value, this depends on scale being set
   			my = (float)magCount[1]*mRes*magCalibration[1] - magBias[1];
   			mz = (float)magCount[2]*mRes*magCalibration[2] - magBias[2];

			float heading = (atan2(my, mx)*180.0/3.141592)+90;
			if (heading < 0.0) heading = heading+360.0;
//			printf("mx, my, mz = %f, %f, %f\n", mx, my, mz);
//			printf("heading: %f\n", heading);
			UART0_IMU_send(heading);

//   			mx += (float)magCount[0]*mRes*magCalibration[0] - magBias[0];  // get actual magnetometer value, this depends on scale being set
//   			my += (float)magCount[1]*mRes*magCalibration[1] - magBias[1];
//   			mz += (float)magCount[2]*mRes*magCalibration[2] - magBias[2];
//			if(++count == 10){
//				mx = mx / 10.0;
//				my = my / 10.0;
//				mz = mz / 10.0;
//				float heading = (atan2(my, mx)*180.0/3.141592)+90;
//				if (heading < 0.0) heading = heading+360.0;
//				printf("mx, my, mz = %f, %f, %f\n", mx, my, mz);
//				printf("heading: %f\n", heading);
//				mx = 0.0;
//				my = 0.0;
//				mz = 0.0;
//				count =0;
//			}
		}
		if(GPS_parsing(s)==1 && Timer0_flag(500)==1){
			UART0_GPS_send(s);
		}
		switch(UART0_parsing(s)){
			case 1:
			{
				printf("%d\n", s[3]*100+s[4]*10+s[5]);
				break;
			}
			case 2:
			{
				unsigned char comma_idx = 0;
				float L_speed = 0;
				float R_speed = 0;
				for(unsigned char i=3; s[i]!= ','; i++){
					L_speed += (s[i]-'0')*round(pow(10.0, (float)(i-3)));
					comma_idx = i;
				}
				for(unsigned char i=comma_idx+2; s[i]!= '*'; i++){
					R_speed += (s[i]-'0')*round(pow(10.0, (float)(i-(comma_idx+2))));
				}
				xm430_Goal_velocity_action(0x01, 0x02, (int)L_speed-1024, (int)R_speed-1024);
//				printf("%d, %d\n", (int)L_speed-1024, (int)R_speed-1024);
				break;				
			}
		}
	}
}