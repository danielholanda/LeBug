 //-----------------------------------------------------
 // Design Name : Vector Scalar Reduce Unit
 // Function    : Reduces an N-size vector into N, M or 1 values
 //-----------------------------------------------------

 module  vectorScalarReduceUnit #(
  parameter N=8,
  parameter DATA_WIDTH=32,
  )
  (
  input logic clk,
  input logic valid_in,
  input logic eof_in,
  input logic [DATA_WIDTH-1:0] vector_in [N-1:0],
  output reg valid_out,
  output reg [DATA_WIDTH-1:0] vector_out [N-1:0]
 );

    //----------Internal Variables------------


    //-------------Code Start-----------------

    always @(posedge clk) begin
      
        // Assign outputs
        valid_out<=valid_in;
    end

 
 endmodule 