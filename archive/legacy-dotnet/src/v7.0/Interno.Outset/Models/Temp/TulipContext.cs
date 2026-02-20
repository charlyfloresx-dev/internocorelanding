using System;
using System.Collections.Generic;
using Microsoft.EntityFrameworkCore;

namespace Interno.Outset.Models.Temp;

public partial class TulipContext : DbContext
{
    public TulipContext()
    {
    }

    public TulipContext(DbContextOptions<TulipContext> options)
        : base(options)
    {
    }

    public virtual DbSet<ProductionOutput> ProductionOutputs { get; set; }

    //     protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
    // #warning To protect potentially sensitive information in your connection string, you should move it out of source code. You can avoid scaffolding the connection string by using the Name= syntax to read it from configuration - see https://go.microsoft.com/fwlink/?linkid=2131148. For more guidance on storing connection strings, see http://go.microsoft.com/fwlink/?LinkId=723263.
    //         => optionsBuilder.UseMySql("server=tj-it-win10x01;database=tulip;user=interno_server;password=37090uts3t;treattinyasboolean=true;allowzerodatetime=True;convertzerodatetime=True", Microsoft.EntityFrameworkCore.ServerVersion.Parse("8.0.33-mysql"));

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder
            .UseCollation("utf8mb4_0900_ai_ci")
            .HasCharSet("utf8mb4");

        modelBuilder.Entity<ProductionOutput>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("PRIMARY");

            entity.ToTable("#production output");

            entity.Property(e => e.Id)
                .HasMaxLength(150)
                .HasColumnName("id");
            entity.Property(e => e.CreatedAt)
                .HasColumnType("timestamp")
                .HasColumnName("_createdAt");
            entity.Property(e => e.Start)
                .HasColumnType("timestamp")
                .HasColumnName("dyvxc_start");
            entity.Property(e => e.Line)
                .HasColumnType("text")
                .HasColumnName("egukd_line");
            entity.Property(e => e.Area)
                .HasColumnType("text")
                .HasColumnName("feibo_area");
            entity.Property(e => e.End)
                .HasColumnType("timestamp")
                .HasColumnName("ftcdw_end");
            entity.Property(e => e.PartNumber)
                .HasColumnType("text")
                .HasColumnName("ioyqv_part_number");
            entity.Property(e => e.Station)
                .HasColumnType("text")
                .HasColumnName("jabzi_station");
            entity.Property(e => e.Eficiency)
                .HasPrecision(16, 4)
                .HasColumnName("kxakg_eficiency");
            entity.Property(e => e.Time)
                .HasPrecision(16, 4)
                .HasColumnName("lelei_time");
            entity.Property(e => e.Collaborator)
                .HasColumnType("text")
                .HasColumnName("lmdpo_collaborator");
            entity.Property(e => e.Date)
                .HasColumnType("timestamp")
                .HasColumnName("lwxmj_date");
            entity.Property(e => e.SerialNumber)
                .HasColumnType("text")
                .HasColumnName("njtqf_serial_number");
            entity.Property(e => e.SequenceNumber).HasColumnName("_sequenceNumber");
            entity.Property(e => e.UpdatedAt)
                .HasColumnType("timestamp")
                .HasColumnName("_updatedAt");

            entity.Property(e => e.StdTime)
                .HasPrecision(16, 4)
                .HasColumnName("wpbfj_std_time");
        });

        OnModelCreatingPartial(modelBuilder);
    }

    partial void OnModelCreatingPartial(ModelBuilder modelBuilder);
}
