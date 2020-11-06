 //-----------------------------------------------------
 // Design Name : Data Packer
 // Function    : Packs data into N values by receiving blocks of N, M or 1 values
 //-----------------------------------------------------

 module  dataPacker #(
  parameter N=8,
  parameter M=2,
  parameter DATA_WIDTH=32,
  parameter MAX_CHAINS=4,
  parameter PERSONAL_CONFIG_ID=0,
  parameter [7:0] INITIAL_FIRMWARE      [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}},
  parameter [7:0] INITIAL_FIRMWARE_COND [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}}
  )
  (
  input logic clk,
  input logic tracing,
  input logic valid_in,
  input logic eof_in,
  input logic bof_in,
  input logic [$clog2(MAX_CHAINS)-1:0] chainId_in,
  input logic [7:0] configId,
  input logic [7:0] configData,
  input logic [DATA_WIDTH-1:0] vector_in [N-1:0],
  output reg [DATA_WIDTH-1:0] vector_out [N-1:0],
  output reg valid_out
 );

    //----------Internal Variables------------
    reg [7:0] firmware_cond       [0:MAX_CHAINS-1] = INITIAL_FIRMWARE_COND;
    reg [DATA_WIDTH-1:0] packed_data [N-1:0];
    reg [31:0] packed_counter = 0;
    reg [7:0] firmware [0:MAX_CHAINS-1] = INITIAL_FIRMWARE;
    reg [31:0] total_length;
    reg [31:0] vector_length;
    reg commit;
    reg cond_valid;
    wire [DATA_WIDTH-1:0] pack_1 [N-1:0];
    wire [DATA_WIDTH-1:0] pack_M [N-1:0];
    reg [7:0] byte_counter=0;

    //-------------Code Start-----------------

    always @(posedge clk) begin
      //Packing is not perfect, otherwise it would be too expensive
      // If we overflow, we just submit things as they are (This may happen if we are mixing precisions)
      if (valid_in==1'b1 && tracing==1'b1 && commit==1'b1 && cond_valid==1'b1) begin
        if (total_length>N) begin 
            vector_out<=packed_data;
            packed_data<=vector_in;
            valid_out<=1;
            packed_counter<=vector_length;
        end
        else if (total_length==N) begin 
            if (vector_length==1) begin
              vector_out<=pack_1;
            end
            else if (vector_length==M) begin
              vector_out<=pack_M;
            end
            else begin
              vector_out<=vector_in;
            end
            packed_data<='{default:'{DATA_WIDTH{0}}};
            packed_counter<=0;
            valid_out<=1;
        end
        else begin //no vector overflow
          valid_out<=0;
          if (vector_length==1) begin
            packed_data<=pack_1;
            packed_counter<=total_length;
          end
          else if (vector_length==M) begin
            packed_data<=pack_M;
            packed_counter<=total_length;
          end
        end
      end
      else begin
        valid_out<=0;
        if (tracing==1'b0) begin // If we are not tracing, we are reconfiguring the instrumentation
          if (configId==PERSONAL_CONFIG_ID) begin
            byte_counter<=byte_counter+1;
            if (byte_counter<MAX_CHAINS)begin
              firmware_cond[byte_counter]=configData;
            end
            else if (byte_counter<MAX_CHAINS*2)begin
              firmware[byte_counter]=configData;
            end
          end
          else begin
            byte_counter<=0;
          end
        end
      end
        //$display("New Cycle:");
        //$display("\tvector_in: %0d %0d %0d %0d %0d %0d %0d %0d (valid = %d)",vector_in[0],vector_in[1],vector_in[2],vector_in[3],vector_in[4],vector_in[5],vector_in[6],vector_in[7],valid_in);
        //$display("\tpacked_data: %0d %0d %0d %0d %0d %0d %0d %0d",packed_data[0],packed_data[1],packed_data[2],packed_data[3],packed_data[4],packed_data[5],packed_data[6],packed_data[7]);
        //$display("\tvector_out: %0d %0d %0d %0d %0d %0d %0d %0d (valid = %d)",vector_out[0],vector_out[1],vector_out[2],vector_out[3],vector_out[4],vector_out[5],vector_out[6],vector_out[7],valid_out);
    end

    always @(*) begin
      case (firmware [chainId_in])
        8'd0:    begin vector_length = N; commit=1; end
        8'd1:    begin vector_length = M; commit=1; end
        8'd2:    begin vector_length = 1; commit=1; end
        default: begin vector_length = 0; commit=0; end
      endcase

      // Only perform operation if condition is valid
      // none=0, last=1, notlast=2, first=3, notfirst=4
      if (firmware_cond[chainId_in]==8'd0 | (firmware_cond[chainId_in]==8'd1 & eof_in==1'b1) | (firmware_cond[chainId_in]==8'd2 & eof_in==1'b0) |  (firmware_cond[chainId_in]==8'd3 & bof_in==1'b1) | (firmware_cond[chainId_in]==8'd4 & bof_in==1'b0)) begin
        cond_valid = 1'b1;
      end
      else begin
        cond_valid = 1'b0;
      end
    end

    assign total_length = packed_counter+vector_length;
    assign pack_1 = {vector_in[0],packed_data[N-1:1]};
    assign pack_M = {vector_in[M-1:0],packed_data[N-1:M]};
 
 endmodule 