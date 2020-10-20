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
  parameter [7:0] INITIAL_FIRMWARE [0:MAX_CHAINS-1] = '{MAX_CHAINS{0}}
  )
  (
  input logic clk,
  input logic tracing,
  input logic valid_in,
  input logic eof_in,
  input logic chainId_in,
  input logic [7:0] configId,
  input logic [7:0] configData,
  input logic [DATA_WIDTH-1:0] vector_in [N-1:0],
  output reg [DATA_WIDTH-1:0] vector_out [N-1:0],
  output reg valid_out
 );

    //----------Internal Variables------------
    reg [DATA_WIDTH-1:0] packed_data [N*2-1:0];
    reg [31:0] packed_counter = 0;
    reg [7:0] firmware [0:MAX_CHAINS-1] = INITIAL_FIRMWARE;
    reg [31:0] total_length;
    reg [31:0] vector_length;
    reg commit;

    //-------------Code Start-----------------

    always @(posedge clk) begin
      //Packing is not perfect, otherwise it would be too expensive
      // If we overflow, we just submit things as they are (This may happen if we are mixing precisions)
      if (valid_in==1'b1 && tracing==1'b1 && commit==1'b1) begin
        $display("vector_length %d",vector_length);
        $display("total_length %d",total_length);
        $display("packed_counter %d",packed_counter);
        if (total_length>N) begin 
            vector_out<=packed_data;
            packed_data<=vector_in;
            valid_out<=1;
            packed_counter<=vector_length;
        end
        else if (total_length==N) begin 
            valid_out<=1;
            vector_out<=vector_in;
            packed_data<='{default:'{DATA_WIDTH{0}}};
            packed_counter<=0;
        end
        else begin //no vector overflow
          valid_out<=0;
          if (vector_length==1) begin
            packed_data<={vector_in[0],packed_data[N-1:1]};
            packed_counter<=total_length;
          end
          else if (vector_length==M) begin
            packed_data<={vector_in[M-1:0],packed_data[N-1:M]};
            packed_counter<=total_length;
          end
        end
      end
      else begin
        valid_out<=0;
      end
    end

    always @(*) begin
      case (firmware [chainId_in])
        8'd0:    begin vector_length = N; commit=1; end
        8'd1:    begin vector_length = M; commit=1; end
        8'd2:    begin vector_length = 1; commit=1; end
        default: begin vector_length = 0; commit=0; end
      endcase
    end

    assign total_length = packed_counter+vector_length;
 
 endmodule 