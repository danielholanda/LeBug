 //-----------------------------------------------------
 // Design Name : Data Packer
 // Function    : Packs data into N values by receiving blocks of N, M or 1 values
 //-----------------------------------------------------

 module  DataPacker #(
  parameter DATA_WIDTH=32
  )
  (
  input logic clk,
  input logic tracing,
  input logic valid_in,
  input logic [DATA_WIDTH-1:0] vector_in [N-1:0],
  output reg [DATA_WIDTH-1:0] vector_out [N-1:0],
  output reg valid_out,
 );

    //----------Internal Variables------------


    //-------------Code Start-----------------

    always @(posedge clk) begin

    end


 
 endmodule 