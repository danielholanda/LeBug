 //-----------------------------------------------------
 // Design Name : Input Buffer
 // Function    : Buffers vectors for up to D cycles
 //-----------------------------------------------------
 module  input_buffer #(
  parameter N = 8,
  parameter DATA_WIDTH = 32,
  parameter IB_DEPTH = 8
  )
  (
  input logic clk_in,
  input logic valid_in,
  input logic eof_in,
  input logic [DATA_WIDTH-1:0] vector_in [N-1:0],
  output logic valid_out,
  output logic eof_out,
  output logic [DATA_WIDTH-1:0] vector_out [N-1:0]
 );
 //-------------Code Start-----------------

    assign valid_out = valid_in;
    assign eof_out=eof_in;
    assign vector_out=vector_in;
 
 endmodule 