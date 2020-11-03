 //-----------------------------------------------------
 // Design Name : Reconfig unit
 // Function    : Receive UART data, reconfigure all blocks and dump trace buffer data when needed
 //-----------------------------------------------------

module  reconfigUnit 
  (
  input logic clk,
  input logic [7:0] rx_data,
  input logic new_rx_data,
  output logic [7:0] tx_data,
  output logic new_tx_data,
  input logic tx_busy,
  output logic tracing,
  output logic [7:0] configId,
  output logic [7:0] configData

 );

	assign tracing=1'b1;
	assign configId=8'd0;
	assign configData=8'd0;

	assign tx_data=8'd0;
	assign new_tx_data=1'b0;


 endmodule 