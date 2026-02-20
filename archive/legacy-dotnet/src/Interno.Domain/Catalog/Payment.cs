using System.ComponentModel.DataAnnotations;
namespace Interno.Domain.Catalog
{
    public class Payment
    {
        [Key]
        public int Id { get; set; }
        [Required(ErrorMessage = "You should provide a Payment Method name.")]
        [MaxLength(45)]
        public string Method { get; set; }
        [MaxLength(250)]
        public string Description { get; set; }
    }
    /*
    '1', 'Cash Payment', ''
    '2', 'Credit Card', ''
    '3', 'Bank Tranfer', ''
    '4', 'Online Bank Transfer', ''
    '5', 'E-wallets', ''
    */
}