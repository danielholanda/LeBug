//-----------------------------------------------------
// Design Name : Vector Scalar Reduce Unit
// Function    : Reduces an N-size vector into N, M or 1 values
//-----------------------------------------------------

`include "adder_tree.sv"

module  vectorScalarReduceUnit #(
  parameter N=8,
  parameter DATA_WIDTH=32,
  parameter MAX_CHAINS=4,
  parameter PERSONAL_CONFIG_ID=0,
  parameter [7:0] INITIAL_FIRMWARE [MAX_CHAINS-1:0] = '{MAX_CHAINS{0}}
  )
  (
  input logic clk,
  input logic valid_in,
  input logic eof_in,
  input logic chainId_in,
  input logic tracing,
  input logic [7:0] configId,
  input logic [7:0] configData,
  input logic [DATA_WIDTH-1:0] vector_in [N-1:0],
  output reg valid_out,
  output reg [DATA_WIDTH-1:0] vector_out [N-1:0]
 );

    //----------Internal Variables------------
    reg [7:0] firmware [MAX_CHAINS-1:0] = INITIAL_FIRMWARE;
    wire [DATA_WIDTH-1:0] sum; 
    reg [DATA_WIDTH-1:0] zeros [N-1:0]='{N{0}};


    //-------------Code Start-----------------

    adderTree #(.N(N), .DATA_WIDTH(DATA_WIDTH))
          adder_tree_inst(.vector(vector_in), .result(sum));

    always @(posedge clk) begin
        // Perform operations normally if we are tracing
        if (tracing==1'b1) begin
          // Assign outputs
          valid_out<=valid_in;
          // Return N bytes (pass through)
          if (firmware[chainId_in]==8'd0) begin
              vector_out<=vector_in;
          end
          // Return 1 element (sum of all) zero padded
          else if (firmware[chainId_in]==8'd1) begin
            vector_out<=zeros;
            vector_out[0]<= sum;
          end
        end

        // If we are not tracing, we are reconfiguring the instrumentation
        else begin
          if (configId==PERSONAL_CONFIG_ID && configId<PERSONAL_CONFIG_ID+MAX_CHAINS)begin
            firmware[chainId_in]=configData;
          end
        end
    end

 
endmodule 