 //-----------------------------------------------------
 // Design Name : UART
 // Function    : Interfaces with PC and configures all building blocks
 //-----------------------------------------------------

module uart (
	input logic clk,
	output logic tracing,
  	output logic [7:0] configId,
  	output logic [7:0] configData
);

    assign tracing=1'b1;
	assign configId=8'd0;
	assign configData=8'd0;
	

endmodule 


