//-----------------------------------------------------
// Design Name : Vector Scalar Reduce Unit
// Function    : Reduces an N-size vector into N, M or 1 values
//-----------------------------------------------------

`include "adder_tree.sv"

module  vectorScalarReduceUnit #(
  parameter N=8,
  parameter DATA_WIDTH=32
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
    reg [7:0] conf_byte=8'd1;
    wire [DATA_WIDTH-1:0] sum; 
    reg [DATA_WIDTH-1:0] zeros [N-1:0]='{N{0}};


    //-------------Code Start-----------------

    adderTree #(.N(N), .DATA_WIDTH(DATA_WIDTH))
          adder_tree_inst(.vector(vector_in), .result(sum));

    always @(posedge clk) begin

        // Assign outputs
        valid_out<=valid_in;

        // Return N bytes
        if (conf_byte==8'd0) begin
            vector_out<=vector_in;
        end
        // Return 1 element (sum of all) zero padded
        else if (conf_byte==8'd1) begin
          vector_out<=zeros;
          vector_out[0]<= sum;
        end
    end

 
endmodule 