 //-----------------------------------------------------
 // Design Name : UART
 // Function    : Interfaces with PC and send data to cofiguration block
 //-----------------------------------------------------


//---------------------------------------------------------------------------------------
// uart top level module  
// baud rate generator parameters for 57600 baud on 50MHz clock 
// baud_freq = 16*baud_rate / gcd(global_clock_freq, 16*baud_rate)
// baud_limit = (global_clock_freq / gcd(global_clock_freq, 16*baud_rate)) - baud_freq 
//---------------------------------------------------------------------------------------

module uart
#(
parameter USE_SYNC_RESET = 1,
parameter [15:0] BAUD_LIMIT = 15337,
parameter [11:0] BAUD_FREQ = 288

) 
(
	// global signals 
	clk, reset,
	// uart serial signals 
	uart_rxd, uart_txd,
	// transmit and receive internal interface signals 
	rx_data, new_rx_data, 
	tx_data, new_tx_data, tx_busy
);
//---------------------------------------------------------------------------------------
// modules inputs and outputs 
input 			clk;			// global clk input 
input 			reset;			// global reset input 
input			uart_rxd;		// serial data input 
output			uart_txd;		// serial data output 
input	[7:0]	tx_data;		// data byte to transmit 
input			new_tx_data;	// asserted to indicate that there is a new data byte for transmission 
output 			tx_busy;		// signs that transmitter is busy 
output	[7:0]	rx_data;		// data byte received 
output 			new_rx_data;	// signs that a new byte was received 

// internal wires 
wire ce_16;		// clk enable at bit rate 
wire ser_in;
wire ser_out;

assign ser_in = uart_rxd;
assign ser_out = uart_txd;

//---------------------------------------------------------------------------------------
// module implementation 
// baud rate generator module 
baud_gen 
#(.USE_SYNC_RESET(USE_SYNC_RESET))
baud_gen_1
(
	.clk(clk), .reset(reset), 
	.ce_16(ce_16), .baud_freq(BAUD_FREQ), .baud_limit(BAUD_LIMIT)
);

// uart receiver 
uart_rx
#(.USE_SYNC_RESET(USE_SYNC_RESET))
uart_rx_1 
(
	.clk(clk), .reset(reset), 
	.ce_16(ce_16), .ser_in(ser_in), 
	.rx_data(rx_data), .new_rx_data(new_rx_data) 
);

// uart transmitter 
uart_tx  
#(.USE_SYNC_RESET(USE_SYNC_RESET))
uart_tx_1
(
	.clk(clk), .reset(reset), 
	.ce_16(ce_16), .tx_data(tx_data), .new_tx_data(new_tx_data), 
	.ser_out(ser_out), .tx_busy(tx_busy) 
);

endmodule

//---------------------------------------------------------------------------------------
// baud rate generator for uart 
//
// this module has been changed to receive the baud rate dividing counter from registers.
// the two registers should be calculated as follows:
// first register:
// 		baud_freq = 16*baud_rate / gcd(global_clk_freq, 16*baud_rate)
// second register:
// 		baud_limit = (global_clk_freq / gcd(global_clk_freq, 16*baud_rate)) - baud_freq 
//
//---------------------------------------------------------------------------------------

module baud_gen 
#(
parameter USE_SYNC_RESET = 0
) 
(
	clk, reset, 
	ce_16, baud_freq, baud_limit 
);
//---------------------------------------------------------------------------------------
// modules inputs and outputs 
input 			clk;		// global clk input 
input 			reset;		// global reset input 
output			ce_16;		// baud rate multiplyed by 16 
input	[11:0]	baud_freq;	// baud rate setting registers - see header description 
input	[15:0]	baud_limit;

// internal registers 
reg ce_16;
reg [15:0]	counter;
generate
				if (USE_SYNC_RESET)
				begin
				    //---------------------------------------------------------------------------------------
					// module implementation 
					// baud divider counter  
					always @ (posedge clk)
					begin
						if (reset) 
							counter <= 16'b0;
						else if (counter >= baud_limit) 
							counter <= counter - baud_limit;
						else 
							counter <= counter + baud_freq;
					end

					// clk divider output 
					always @ (posedge clk)
					begin
						if (reset)
							ce_16 <= 1'b0;
						else if (counter >= baud_limit) 
							ce_16 <= 1'b1;
						else 
							ce_16 <= 1'b0;
					end 
				end else
				begin
					//---------------------------------------------------------------------------------------
					// module implementation 
					// baud divider counter  
					always @ (posedge clk or posedge reset)
					begin
						if (reset) 
							counter <= 16'b0;
						else if (counter >= baud_limit) 
							counter <= counter - baud_limit;
						else 
							counter <= counter + baud_freq;
					end

					// clk divider output 
					always @ (posedge clk or posedge reset)
					begin
						if (reset)
							ce_16 <= 1'b0;
						else if (counter >= baud_limit) 
							ce_16 <= 1'b1;
						else 
							ce_16 <= 1'b0;
					end 
			end 
endgenerate

endmodule

//---------------------------------------------------------------------------------------
// uart transmit module  
//
//---------------------------------------------------------------------------------------

module uart_tx
#(
parameter USE_SYNC_RESET = 0
)  
(
	clk, reset,
	ce_16, tx_data, new_tx_data, 
	ser_out, tx_busy
);
//---------------------------------------------------------------------------------------
// modules inputs and outputs 
input 			clk;			// global clk input 
input 			reset;			// global reset input 
input			ce_16;			// baud rate multiplyed by 16 - generated by baud module 
input	[7:0]	tx_data;		// data byte to transmit 
input			new_tx_data;	// asserted to indicate that there is a new data byte for transmission 
output			ser_out;		// serial data output 
output 			tx_busy;		// signs that transmitter is busy 

// internal wires 
wire ce_1;		// clk enable at bit rate 

// internal registers 
reg ser_out = 1'b1;
reg tx_busy;
reg [3:0]	count16;
reg [3:0]	bit_count;
reg [8:0]	data_buf;

generate
				if (USE_SYNC_RESET)
				begin
				//---------------------------------------------------------------------------------------
								// module implementation 
								// a counter to count 16 pulses of ce_16 to generate the ce_1 pulse 
								always @ (posedge clk)
								begin
									if (reset) 
										count16 <= 4'b0;
									else if (tx_busy & ce_16)
										count16 <= count16 + 4'b1;
									else if (~tx_busy)
										count16 <= 4'b0;
								end 

								// ce_1 pulse indicating output data bit should be updated 
								assign ce_1 = (count16 == 4'b1111) & ce_16;

								// tx_busy flag 
								always @ (posedge clk)
								begin
									if (reset) 
										tx_busy <= 1'b0;
									else if (~tx_busy & new_tx_data)
										tx_busy <= 1'b1;
									else if (tx_busy & (bit_count == 4'h9) & ce_1)
										tx_busy <= 1'b0;
								end 

								// output bit counter 
								always @ (posedge clk)
								begin
									if (reset) 
										bit_count <= 4'h0;
									else if (tx_busy & ce_1)
										bit_count <= bit_count + 4'h1;
									else if (~tx_busy) 
										bit_count <= 4'h0;
								end 

								// data shift register 
								always @ (posedge clk)
								begin
									if (reset) 
										data_buf <= 9'b0;
									else if (~tx_busy)
										data_buf <= {tx_data, 1'b0};
									else if (tx_busy & ce_1)
										data_buf <= {1'b1, data_buf[8:1]};
								end 

								// output data bit 
								always @ (posedge clk)
								begin
									if (reset) 
										ser_out <= 1'b1;
									else if (tx_busy)
										ser_out <= data_buf[0];
									else 
										ser_out <= 1'b1;
								end 
				end else
				begin
								//---------------------------------------------------------------------------------------
								// module implementation 
								// a counter to count 16 pulses of ce_16 to generate the ce_1 pulse 
								always @ (posedge clk or posedge reset)
								begin
									if (reset) 
										count16 <= 4'b0;
									else if (tx_busy & ce_16)
										count16 <= count16 + 4'b1;
									else if (~tx_busy)
										count16 <= 4'b0;
								end 

								// ce_1 pulse indicating output data bit should be updated 
								assign ce_1 = (count16 == 4'b1111) & ce_16;

								// tx_busy flag 
								always @ (posedge clk or posedge reset)
								begin
									if (reset) 
										tx_busy <= 1'b0;
									else if (~tx_busy & new_tx_data)
										tx_busy <= 1'b1;
									else if (tx_busy & (bit_count == 4'h9) & ce_1)
										tx_busy <= 1'b0;
								end 

								// output bit counter 
								always @ (posedge clk or posedge reset)
								begin
									if (reset) 
										bit_count <= 4'h0;
									else if (tx_busy & ce_1)
										bit_count <= bit_count + 4'h1;
									else if (~tx_busy) 
										bit_count <= 4'h0;
								end 

								// data shift register 
								always @ (posedge clk or posedge reset)
								begin
									if (reset) 
										data_buf <= 9'b0;
									else if (~tx_busy)
										data_buf <= {tx_data, 1'b0};
									else if (tx_busy & ce_1)
										data_buf <= {1'b1, data_buf[8:1]};
								end 

								// output data bit 
								always @ (posedge clk or posedge reset)
								begin
									if (reset) 
										ser_out <= 1'b1;
									else if (tx_busy)
										ser_out <= data_buf[0];
									else 
										ser_out <= 1'b1;
								end 
				end
endgenerate

endmodule

//---------------------------------------------------------------------------------------
// uart receive module  
//
//---------------------------------------------------------------------------------------

module uart_rx
#(
parameter USE_SYNC_RESET = 0
)  
(
	clk, reset,
	ce_16, ser_in, 
	rx_data, new_rx_data 
);
//---------------------------------------------------------------------------------------
// modules inputs and outputs 
input 			clk;			// global clk input 
input 			reset;			// global reset input 
input			ce_16;			// baud rate multiplyed by 16 - generated by baud module 
input			ser_in;			// serial data input 
output	[7:0]	rx_data;		// data byte received 
output 			new_rx_data;	// signs that a new byte was received 

// internal wires 
wire ce_1;		// clk enable at bit rate 
wire ce_1_mid;	// clk enable at the middle of each bit - used to sample data 

// internal registers 
reg	[7:0] rx_data;
(* keep = 1, preserve = 1 *) reg	new_rx_data;
reg in_sync0;
reg [1:1] in_sync;
reg rx_busy; 
reg [3:0]	count16;
reg [3:0]	bit_count;
reg [7:0]	data_buf;

generate
if (USE_SYNC_RESET)
begin
					//---------------------------------------------------------------------------------------
					// module implementation 
					// input async input is sampled twice 
					always @ (posedge clk)
					begin 
						if (reset) 
						begin
							in_sync[1] <= 1'b1;
							in_sync0   <= 1'b1;
						end
						else 
						begin
							in_sync0 <= ser_in;
							in_sync[1] <= in_sync0;
						end
					end 

					// a counter to count 16 pulses of ce_16 to generate the ce_1 and ce_1_mid pulses.
					// this counter is used to detect the start bit while the receiver is not receiving and 
					// signs the sampling cycle during reception. 
					always @ (posedge clk)
					begin
						if (reset) 
							count16 <= 4'b0;
						else if (ce_16) 
						begin 
							if (rx_busy | (in_sync[1] == 1'b0))
								count16 <= count16 + 4'b1;
							else 
								count16 <= 4'b0;
						end 
					end 

					// ce_1 pulse indicating expected end of current bit 
					assign ce_1 = (count16 == 4'b1111) & ce_16;
					// ce_1_mid pulse indication the sampling clk cycle of the current data bit 
					assign ce_1_mid = (count16 == 4'b0111) & ce_16;

					// receiving busy flag 
					always @ (posedge clk)
					begin 
						if (reset)
							rx_busy <= 1'b0;
						else if (~rx_busy & ce_1_mid)
							rx_busy <= 1'b1;
						else if (rx_busy & (bit_count == 4'h8) & ce_1_mid) 
							rx_busy <= 1'b0;
					end 

					// bit counter 
					always @ (posedge clk)
					begin 
						if (reset)
							bit_count <= 4'h0;
						else if (~rx_busy) 
							bit_count <= 4'h0;
						else if (rx_busy & ce_1_mid)
							bit_count <= bit_count + 4'h1;
					end 

					// data buffer shift register 
					always @ (posedge clk)
					begin 
						if (reset)
							data_buf <= 8'h0;
						else if (rx_busy & ce_1_mid)
							data_buf <= {in_sync[1], data_buf[7:1]};
					end 

					// data output and flag 
					always @ (posedge clk)
					begin 
						if (reset) 
						begin 
							rx_data <= 8'h0;
							new_rx_data <= 1'b0;
						end 
						else if (rx_busy & (bit_count == 4'h8) & ce_1)
						begin 
							rx_data <= data_buf;
							new_rx_data <= 1'b1;
						end 
						else 
							new_rx_data <= 1'b0;
					end 

end else
begin
					//---------------------------------------------------------------------------------------
					// module implementation 
					// input async input is sampled twice 
					always @ (posedge clk or posedge reset)
					begin 
						if (reset) 
						begin
							in_sync[1] <= 1'b1;
							in_sync0   <= 1'b1;
						end
						else 
						begin
							in_sync0 <= ser_in;
							in_sync[1] <= in_sync0;
						end
					end 

					// a counter to count 16 pulses of ce_16 to generate the ce_1 and ce_1_mid pulses.
					// this counter is used to detect the start bit while the receiver is not receiving and 
					// signs the sampling cycle during reception. 
					always @ (posedge clk or posedge reset)
					begin
						if (reset) 
							count16 <= 4'b0;
						else if (ce_16) 
						begin 
							if (rx_busy | (in_sync[1] == 1'b0))
								count16 <= count16 + 4'b1;
							else 
								count16 <= 4'b0;
						end 
					end 

					// ce_1 pulse indicating expected end of current bit 
					assign ce_1 = (count16 == 4'b1111) & ce_16;
					// ce_1_mid pulse indication the sampling clk cycle of the current data bit 
					assign ce_1_mid = (count16 == 4'b0111) & ce_16;

					// receiving busy flag 
					always @ (posedge clk or posedge reset)
					begin 
						if (reset)
							rx_busy <= 1'b0;
						else if (~rx_busy & ce_1_mid)
							rx_busy <= 1'b1;
						else if (rx_busy & (bit_count == 4'h8) & ce_1_mid) 
							rx_busy <= 1'b0;
					end 

					// bit counter 
					always @ (posedge clk or posedge reset)
					begin 
						if (reset)
							bit_count <= 4'h0;
						else if (~rx_busy) 
							bit_count <= 4'h0;
						else if (rx_busy & ce_1_mid)
							bit_count <= bit_count + 4'h1;
					end 

					// data buffer shift register 
					always @ (posedge clk or posedge reset)
					begin 
						if (reset)
							data_buf <= 8'h0;
						else if (rx_busy & ce_1_mid)
							data_buf <= {in_sync[1], data_buf[7:1]};
					end 

					// data output and flag 
					always @ (posedge clk or posedge reset)
					begin 
						if (reset) 
						begin 
							rx_data <= 8'h0;
							new_rx_data <= 1'b0;
						end 
						else if (rx_busy & (bit_count == 4'h8) & ce_1)
						begin 
							rx_data <= data_buf;
							new_rx_data <= 1'b1;
						end 
						else 
							new_rx_data <= 1'b0;
					end 
end
endgenerate
endmodule



